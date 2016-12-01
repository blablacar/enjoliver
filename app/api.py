import os
import urllib2

from flask import Flask, request, json, jsonify
from sqlalchemy import create_engine
from werkzeug.contrib.cache import SimpleCache

import crud
import model

app = application = Flask(__name__)

application.config["BOOTCFG_URI"] = os.getenv(
    "BOOTCFG_URI", "http://127.0.0.1:8080")

application.config["DB_PATH"] = os.getenv(
    "DB_PATH", 'sqlite:///%s/db.sqlite' % os.path.dirname(os.path.abspath(__file__)))

engine = None

if __name__ == '__main__' or (os.getenv("SERVER_SOFTWARE") is not None and "gunicorn" in os.getenv("SERVER_SOFTWARE")):
    engine = create_engine(application.config["DB_PATH"])
    model.Base.metadata.create_all(engine)

# application.config["FS_CACHE"] = os.getenv(
#     "FS_CACHE", "/tmp")

# cache = FileSystemCache(application.config["FS_CACHE"])

cache = SimpleCache()

application.config["BOOTCFG_URLS"] = [
    "/",
    "/boot.ipxe",
    "/boot.ipxe.0",
    "/assets"
]


@application.route('/', methods=['GET'])
def root():
    """
    Map the API
    :return: available routes
    """
    links = [l for l in set([k.rule for k in app.url_map.iter_rules()
                             if "/static/" != k.rule[:8]])]

    return json.jsonify(links)


@application.route('/healthz', methods=['GET'])
def healthz():
    """
    Query all services and return the status
    :return: json
    """
    status = {
        "global": True,
        "flask": True,
        "bootcfg": {
            k: False for k in application.config["BOOTCFG_URLS"]}
    }
    for k in status["bootcfg"]:
        try:
            bootcfg_resp = urllib2.urlopen(
                "%s%s" % (app.config["BOOTCFG_URI"], k))
            assert bootcfg_resp.code == 200
            status["bootcfg"][k] = True
        except Exception:
            status["bootcfg"][k] = False
            status["global"] = False

    app.logger.debug("%s" % status)
    return json.jsonify(status)


@application.route('/discovery', methods=['POST'])
def discovery():
    if request.content_type != "application/json":
        try:
            r = json.loads(request.data)
        except ValueError:
            app.logger.error("ValueError for %s" % request.data)
            return jsonify(
                {
                    u'boot-info': {},
                    u'lldp': {},
                    u'interfaces': []
                }), 400
    else:
        r = request.get_json()

    app.logger.debug("application/json \"%s\"" % r)

    print r
    try:
        i = crud.Inject(engine=engine, discovery=r)
        new = i.commit_and_close()
        return jsonify({"total_elt": new[0], "new": new[1]})

    except (KeyError, TypeError):
        return jsonify(
            {
                u'boot-info': {},
                u'lldp': {},
                u'interfaces': []
            }), 406


@application.route('/discovery', methods=['GET'])
def discovery_get():
    fetch = crud.Fetch(engine=engine)
    all_data = fetch.get_all()

    return jsonify(all_data)


@application.route('/discovery/interfaces', methods=['GET'])
def discovery_interfaces():
    fetch = crud.Fetch(engine=engine)
    interfaces = fetch.get_all_interfaces()

    return jsonify(interfaces)


@application.route('/discovery/ignition-journal/<string:uuid>', methods=['GET'])
def discovery_ignition_journal(uuid):
    fetch = crud.Fetch(engine=engine)
    lines = fetch.get_ignition_journal(uuid)

    return jsonify(lines)


@application.route('/boot.ipxe', methods=['GET'])
@application.route('/boot.ipxe.0', methods=['GET'])
def boot_ipxe():
    """
    Replace the bootcfg/boot.ipxe by insert retry for dhcp and full URL for the chain
    :return: str
    """
    try:
        flask_uri = "%s://%s" % (
            request.environ.get('wsgi.url_scheme'),
            request.environ.get('HTTP_HOST'))
        app.logger.debug("%s" % flask_uri)

    except Exception as e:
        flask_uri = application.config["BOOTCFG_URI"]
        app.logger.warning("%s: fall back to BOOTCFG_URI: %s" % (e.message, flask_uri))

    response = \
        "#!ipxe\n" \
        "echo start /boot.ipxe\n" \
        ":retry_dhcp\n" \
        "dhcp || goto retry_dhcp\n" \
        "chain %s/ipxe?" \
        "uuid=${uuid}&" \
        "mac=${net0/mac:hexhyp}&" \
        "domain=${domain}&" \
        "hostname=${hostname}&" \
        "serial=${serial}\n" % flask_uri
    app.logger.debug("%s" % response)
    return response


@application.route('/ipxe', methods=['GET'])
def ipxe():
    """
    Fetch the bootcfg/ipxe?<key>=<value> and insert retry for dhcp
    :return: str
    """
    try:
        bootcfg_resp = urllib2.urlopen(
            "%s%s" % (
                app.config["BOOTCFG_URI"],
                request.full_path))
        resp_list = bootcfg_resp.readlines()
        bootcfg_resp.close()
        # [ipxe, kernel, initrd, boot]
        if len(resp_list) == 4:
            resp_list.insert(1, "echo start /ipxe\n")
            # resp_list.insert(2, ":retry_dhcp\n")
            # resp_list.insert(3, "dhcp || reboot\n")
        else:
            app.logger.warning("iPXE response is not coherent")

        response = "".join(resp_list)
        app.logger.debug("%s" % response)
        return response, 200

    except urllib2.URLError:
        return "404", 404


@app.errorhandler(404)
def page_not_found(error):
    return '404\n', 404


if __name__ == "__main__":
    app.logger.setLevel("DEBUG")
    application.run(debug=True)
