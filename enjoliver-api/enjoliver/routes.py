import logging
import time

import requests
from flask import Flask, request, json, jsonify, render_template, Response, make_response
from sqlalchemy.orm import sessionmaker
from werkzeug.contrib.cache import BaseCache

from enjoliver import crud, ops, tools
from enjoliver.configs import EnjoliverConfig
from enjoliver.db import session_commit
from enjoliver.model import MachineStates, ScheduleRoles
from enjoliver.repositories.registry import RepositoryRegistry

logger = logging.getLogger(__name__)


def register_routes(
        app: Flask,
        ec: EnjoliverConfig,
        cache: BaseCache,
        sess_maker: sessionmaker,
        registry: RepositoryRegistry):
    """
    Register all of the routes. Functions are sorted by alphabetical order, uri of the route being the key.

    :param app: the Flask app to register routes with
    :param ec: the EnjoliverConfig instance used to get config values
    :param cache: the werkzeug cache instance
    :param sess_maker: the DB session factory
    :param registry: the service registry
    """

    @app.errorhandler(404)
    def not_found(error):
        app.logger.warning("404 on %s" % request.path)
        return Response('404', status=404, mimetype="text/plain")

    @app.route('/', methods=['GET'])
    def api_mapper():
        """
        Map the API
        List all the available routes
        ---
        tags:
          - ops
        responses:
          200:
            description: Routes
            schema:
                type: list
        """
        rules = [k.rule for k in app.url_map.iter_rules()]
        rules = list(set(rules))
        rules.sort()
        return jsonify(rules)

    @app.route('/assets', defaults={'path': ''})
    @app.route('/assets/<path:path>')
    def assets(path):
        """
        Assets server
        Serve the assets
        ---
        tags:
          - matchbox
        responses:
          200:
            description: Content of the asset
          404:
            description: Not valid
            schema:
                type: string
        """
        app.logger.info("%s %s" % (request.method, request.url))
        matchbox_uri = app.config.get("MATCHBOX_URI")
        if matchbox_uri:
            url = "%s/assets/%s" % (matchbox_uri, path)
            matchbox_resp = requests.get(url)
            resp = matchbox_resp.content
            matchbox_resp.close()
            return Response(response=resp, mimetype="application/octet-stream")

        return Response("matchbox=%s" % matchbox_uri, status=404, mimetype="text/plain")

    @app.route('/backup/export', methods=['GET'])
    def backup_as_export():
        """
        Backup by exporting a playbook of what discovery client and schedulers sent to the API
        Allows to just run each entry against the enjoliver API
        Note: it doesnt export the LLDP data eventually stored in the DB
        ---
        tags:
          - ops
        responses:
          200:
            description: Backup playbook
            schema:
                type: list
        """
        return jsonify(crud.BackupExport(sess_maker=sess_maker).get_playbook())

    @app.route('/boot.ipxe', methods=['GET'])
    @app.route('/boot.ipxe.0', methods=['GET'])
    def boot_ipxe():
        """
        iPXE
        ---
        tags:
          - matchbox
        responses:
          200:
            description: iPXE boot script to chain load on /ipxe
            schema:
                type: string
        """
        app.logger.info("%s %s" % (request.method, request.url))
        try:
            flask_uri = app.config["API_URI"]
            if flask_uri is None:
                raise AttributeError("API_URI is None")
            app.logger.debug("%s" % flask_uri)

        except Exception as e:
            flask_uri = app.config["MATCHBOX_URI"]
            app.logger.error("<%s %s>" % (e, type(e)))
            app.logger.warning("Fall back to MATCHBOX_URI: %s" % flask_uri)
            if flask_uri is None:
                raise AttributeError("BOTH API_URI and MATCHBOX_URI are None")

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
        return Response(response, status=200, mimetype="text/plain")

    @app.route("/configs", methods=["GET"])
    @app.route("/config", methods=["GET"])
    def configs():
        """
        Configs
        Returns the current running configuration
        ---
        tags:
          - ops
        responses:
          200:
            description: A JSON of the configuration
        """
        return jsonify(ec.__dict__)

    @app.route('/discovery', methods=['POST'])
    def record_discovery_data():
        """
        Discovery
        Report the current facts of a machine
        ---
        tags:
          - discovery
        responses:
          200:
            description: Number of machines and if the machine is new
            schema:
                type: dict
        """
        app.logger.info("%s %s" % (request.method, request.url))
        err = jsonify({u'boot-info': {}, u'lldp': {}, u'interfaces': [], u"disks": []}), 406
        try:
            discovery_data = json.loads(request.get_data())
        except (KeyError, TypeError, ValueError):
            logger.error("fail to parse discovery data: %s" % request.get_data())
            return err

        try:
            new = registry.discovery.upsert(discovery_data)
            registry.machine_state.update(discovery_data["boot-info"]["mac"], MachineStates.discovery)
            cache.delete(request.path)
            return jsonify({"new-discovery": new}), 200
        except TypeError as e:
            logger.error("fail to store discovery data: %s -> %s" % (request.get_data(), e))
            return err

    @app.route('/discovery', methods=['GET'])
    def get_discovery_data():
        """
        Discovery
        List
        ---
        tags:
          - discovery
        responses:
          200:
            description: Discovery data
            schema:
                type: list
        """
        all_data = cache.get(request.path)
        if not all_data:
            all_data = registry.discovery.fetch_all_discovery()
            cache.set(request.path, all_data, timeout=30)
        return jsonify(all_data)

    @app.route('/healthz', methods=['GET'])
    def healthz():
        """
        Health
        Get the status of the application
        ---
        tags:
          - ops
        responses:
          200:
            description: Components status
            schema:
                type: dict
        """
        data = ops.healthz(app, sess_maker, request)
        res = jsonify(data), 503 if data["global"] is False else 200
        resp = make_response(res)
        resp.headers['Access-Control-Allow-Origin'] = '*'

        return resp

    @app.route("/ignition", methods=["GET"])
    @app.route("/ignition-pxe", methods=["GET"])
    def ignition():
        """
        Ignition
        ---
        tags:
          - matchbox
        responses:
          200:
            description: Ignition configuration
            schema:
                type: dict
          403:
            description: Matchbox unavailable
            schema:
                type: text/plain
          503:
            description: Matchbox is out of sync
            schema:
                type: text/plain
        """
        cache_key = "sync-notify"
        last_sync_ts = cache.get(cache_key)
        app.logger.debug("cacheKey: %s is set with value %s" % (cache_key, last_sync_ts))

        # we ignore the sync status if we arrived from /ignition-pxe because it's a discovery PXE boot
        if last_sync_ts is None and request.path != "/ignition-pxe":
            app.logger.error("matchbox state is out of sync: cacheKey: %s is None" % cache_key)
            return Response("matchbox is out of sync", status=503, mimetype="text/plain")

        if request.path == "/ignition-pxe":
            app.logger.info("%s %s" % (request.method, request.url))

        matchbox_uri = app.config.get("MATCHBOX_URI")
        if matchbox_uri:
            try:
                # remove the -pxe from the path because matchbox only serve /ignition
                path = request.full_path.replace("/ignition-pxe?", "/ignition?")
                matchbox_resp = requests.get("%s%s" % (matchbox_uri, path))
                resp = matchbox_resp.content
                matchbox_resp.close()
                return Response(resp, status=matchbox_resp.status_code, mimetype="text/plain")
            except requests.RequestException as e:
                app.logger.error("fail to query matchbox ignition %s" % e)
                return Response("matchbox doesn't respond", status=502, mimetype="text/plain")

        return Response("matchbox=%s" % matchbox_uri, status=403, mimetype="text/plain")

    @app.route('/ignition/version', methods=['GET'])
    def get_ignition_versions():
        """
        Ignition version
        List the current ignition behind matchbox
        ---
        tags:
          - matchbox
        responses:
          200:
            description: Ignition version
            schema:
                type: list
        """
        return jsonify(cache.get("ignition-version"))

    @app.route('/ignition/version/<string:filename>', methods=['POST'])
    def report_ignition_version(filename):
        """
        Ignition version
        Report the current ignition behind matchbox
        ---
        tags:
          - matchbox
        responses:
          200:
            description: Status of the recorded entry
            schema:
                type: dict
        """
        versions = cache.get("ignition-version")
        if not versions:
            versions = dict()

        new_entry = False if filename in versions.keys() else True
        data = json.loads(request.data)
        versions.update({filename: data[filename]})
        cache.set("ignition-version", versions, timeout=0)
        return jsonify({"new": new_entry, "total": len(versions)})

    @app.route('/install-authorization/<string:request_raw_query>')
    def require_install_authorization(request_raw_query):
        """
        Install Authorization
        Temporize the installation to avoid burst of downloads / extract in memory
        ---
        tags:
          - ops
        responses:
          200:
            description: Granted to install
            schema:
                type: string
          403:
            description: Locked
            schema:
                type: string
        """
        app.logger.info("%s %s %s" % (request.method, request.remote_addr, request.url))
        if ec.coreos_install_lock_seconds > 0:
            lock = cache.get("lock-install")
            if lock is not None:
                app.logger.warning("Locked by %s" % lock)
                registry.machine_state.update(
                    tools.get_mac_from_raw_query(request_raw_query),
                    MachineStates.os_installation_denied
                )
                return Response(response="Locked by %s" % lock, status=403)
            cache.set("lock-install", request_raw_query, timeout=ec.coreos_install_lock_seconds)
            app.logger.info("Granted to %s" % request_raw_query)

        registry.machine_state.update(
            tools.get_mac_from_raw_query(request_raw_query),
            MachineStates.os_installation_granted
        )
        return Response(response="Granted", status=200)

    @app.route('/ipxe', methods=['GET'])
    def ipxe():
        """
        iPXE
        ---
        tags:
          - matchbox
        responses:
          200:
            description: iPXE script
            schema:
                type: string
          404:
            description: Not valid
            schema:
                type: string
        """
        app.logger.info("%s %s" % (request.method, request.url))
        try:
            matchbox_resp = requests.get(
                "%s%s" % (
                    app.config["MATCHBOX_URI"],
                    request.full_path))
            matchbox_resp.close()
            response = matchbox_resp.content.decode()

            mac = request.args.get("mac")
            if mac:
                registry.machine_state.update(mac.replace("-", ":"), MachineStates.booting)

            return Response(response, status=200, mimetype="text/plain")

        except requests.exceptions.ConnectionError:
            app.logger.warning("404 for /ipxe")
            return "404", 404

    @app.route("/lifecycle/coreos-install", methods=["GET"])
    def lifecycle_get_coreos_install_status():
        """
        Lifecycle CoreOS Install
        Get all the CoreOS Install status
        ---
        tags:
          - lifecycle
        responses:
          200:
            description: CoreOS Install status list
            schema:
                type: list
        """
        return jsonify(crud.FetchLifecycle(sess_maker=sess_maker).get_all_coreos_install_status())

    @app.route("/lifecycle/coreos-install/<string:status>/<string:request_raw_query>", methods=["POST"])
    def report_lifecycle_coreos_install(status, request_raw_query):
        """
        Lifecycle CoreOS Install
        Report the status of a CoreOS install by MAC
        ---
        tags:
          - lifecycle
        responses:
          200:
            description: CoreOS Install report
            schema:
                type: dict
        """
        app.logger.info("%s %s" % (request.method, request.url))
        if status.lower() == "success":
            success = True
        elif status.lower() == "fail":
            success = False
        else:
            app.logger.error("%s %s" % (request.method, request.url))
            return "success or fail != %s" % status.lower(), 403

        with session_commit(sess_maker=sess_maker) as session:
            inject = crud.InjectLifecycle(session, request_raw_query=request_raw_query)
            inject.refresh_lifecycle_coreos_install(success)

        registry.machine_state.update(
            mac=tools.get_mac_from_raw_query(request_raw_query),
            state=MachineStates.installation_succeed if success else MachineStates.installation_failed)
        return jsonify({"success": success, "request_raw_query": request_raw_query}), 200

    @app.route("/lifecycle/ignition", methods=["GET"])
    def lifecycle_get_ignition_status():
        """
        Lifecycle Ignition Update
        Get the update status of all Ignition reports
        ---
        tags:
          - lifecycle
        responses:
          200:
            description: Ignition Update status
            schema:
                type: list
        """
        return jsonify(crud.FetchLifecycle(sess_maker=sess_maker).get_all_updated_status())

    @app.route("/lifecycle/ignition/<string:request_raw_query>", methods=["POST"])
    def submit_lifecycle_ignition(request_raw_query):
        """
        Lifecycle Ignition
        ---
        tags:
          - lifecycle
        responses:
          200:
            description: A JSON of the ignition status
        """
        try:
            machine_ignition = json.loads(request.get_data())
        except ValueError:
            app.logger.error("%s have incorrect content" % request.path)
            return jsonify({"message": "FlaskValueError"}), 406
        req = requests.get("%s/ignition?%s" % (ec.matchbox_uri, request_raw_query))
        try:
            matchbox_ignition = json.loads(req.content)
            req.close()
        except ValueError:
            app.logger.error("%s have incorrect matchbox return" % request.path)
            return jsonify({"message": "MatchboxValueError"}), 406

        with session_commit(sess_maker=sess_maker) as session:
            try:
                inject = crud.InjectLifecycle(session, request_raw_query=request_raw_query)
                if json.dumps(machine_ignition, sort_keys=True) == json.dumps(matchbox_ignition, sort_keys=True):
                    inject.refresh_lifecycle_ignition(True)
                    return jsonify({"message": "Up-to-date"}), 200
                else:
                    inject.refresh_lifecycle_ignition(False)
                    return jsonify({"message": "Outdated"}), 210
            except AttributeError:
                return jsonify({"message": "Unknown"}), 406

    @app.route("/lifecycle/rolling", methods=["GET"])
    def lifecycle_rolling_all():
        """
        Lifecycle Rolling Update
        Get the policy list
        ---
        tags:
          - lifecycle
        responses:
          200:
            description: Rolling Update status
            schema:
                type: list
        """
        return jsonify(crud.FetchLifecycle(sess_maker=sess_maker).get_all_rolling_status())

    @app.route("/lifecycle/rolling/<string:request_raw_query>", methods=["GET"])
    def report_lifecycle_rolling(request_raw_query):
        """
        Lifecycle Rolling Update
        Get the current policy for a given machine by UUID or MAC
        ---
        tags:
          - lifecycle
        parameters:
          - name: request_raw_query
            in: path
            description: Pass the mac as 'mac=<mac>'
            required: true
            type: string
        responses:
          403:
            description: mac address is not parsable
            schema:
                type: dict
          200:
            description: Rolling Update is enable
            schema:
                type: dict
          403:
            description: Rolling Update is not enable
            schema:
                type: dict
        """
        life = crud.FetchLifecycle(sess_maker=sess_maker)
        try:
            mac = tools.get_mac_from_raw_query(request_raw_query)
        except AttributeError as e:
            return jsonify({"enable": None, "request_raw_query": "%s:%s" % (request_raw_query, e)}), 403

        allow, strategy = life.get_rolling_status(mac)

        if allow is True:
            return jsonify({"enable": True, "request_raw_query": request_raw_query, "strategy": strategy}), 200
        elif allow is False:
            return jsonify({"enable": False, "request_raw_query": request_raw_query, "strategy": strategy}), 403

        return jsonify({"enable": False, "request_raw_query": request_raw_query, "strategy": None}), 401

    @app.route("/lifecycle/rolling/<string:request_raw_query>", methods=["POST"])
    def change_lifecycle_rolling(request_raw_query):
        """
        Lifecycle Rolling Update
        Change the current policy for a given machine by MAC
        ---
        tags:
          - lifecycle
        parameters:
          - name: request_raw_query
            in: path
            description: Pass the mac as 'mac=<mac>'
            required: true
            type: string
        responses:
          200:
            description: Rolling Update is enable
            schema:
                type: dict
          401:
            description: Mac address is not in database
            schema:
                type: dict
        """

        app.logger.info("%s %s" % (request.method, request.url))
        try:
            strategy = json.loads(request.get_data())["strategy"]
            app.logger.info("%s %s rolling strategy: setting to %s" % (request.method, request.url, strategy))
        except (KeyError, ValueError):
            # JSONDecodeError is a subclass of ValueError
            # Cannot use JSONDecodeError because the import is not consistent between python3.X
            app.logger.info("%s %s rolling strategy: setting default to kexec" % (request.method, request.url))
            strategy = "kexec"

        with session_commit(sess_maker=sess_maker) as session:
            try:
                life = crud.InjectLifecycle(session, request_raw_query)
                life.apply_lifecycle_rolling(True, strategy)
                return jsonify({"enable": True, "request_raw_query": request_raw_query, "strategy": strategy}), 200
            except AttributeError:
                return jsonify({"enable": None, "request_raw_query": request_raw_query, "strategy": strategy}), 401

    @app.route("/lifecycle/rolling/<string:request_raw_query>", methods=["DELETE"])
    def lifecycle_rolling_delete(request_raw_query):
        """
        Lifecycle Rolling Update
        Disable the current policy for a given machine by UUID or MAC
        ---
        tags:
          - lifecycle
        parameters:
          - name: request_raw_query
            in: path
            description: Pass the mac as 'mac=<mac>'
            required: true
            type: string
        responses:
          200:
            description: Rolling Update is not enable
            schema:
                type: dict
        """
        app.logger.info("%s %s" % (request.method, request.url))

        with session_commit(sess_maker=sess_maker) as session:
            life = crud.InjectLifecycle(session, request_raw_query)
            life.apply_lifecycle_rolling(False, None)
            return jsonify({"enable": False, "request_raw_query": request_raw_query}), 200

    @app.route("/metadata", methods=["GET"])
    def metadata():
        """
        Metadata
        ---
        tags:
          - matchbox
        responses:
          200:
            description: Metadata of the current group/profile
            schema:
                type: string
        """
        matchbox_uri = app.config.get("MATCHBOX_URI")
        if matchbox_uri:
            matchbox_resp = requests.get("%s%s" % (matchbox_uri, request.full_path))
            resp = matchbox_resp.content
            matchbox_resp.close()
            return Response(resp, status=matchbox_resp.status_code, mimetype="text/plain")

        return Response("matchbox=%s" % matchbox_uri, status=403, mimetype="text/plain")

    @app.route('/scheduler', methods=['GET'])
    def scheduler_get():
        """
        Scheduler
        List all the running schedules
        ---
        tags:
          - scheduler
        responses:
          200:
            description: Current schedules
            schema:
                type: list
        """
        all_data = cache.get(request.path)
        if all_data is None:
            all_data = registry.machine_schedule.get_all_schedules()
            cache.set(request.path, all_data, timeout=10)

        return jsonify(all_data)

    @app.route('/scheduler', methods=['POST'])
    def scheduler_post():
        """
        Scheduler
        Affect a schedule to a machine
        ---
        tags:
          - scheduler
        responses:
          406:
            description: Incorrect body content
            schema:
                type: dict
          200:
            description: The body sent
            schema:
                type: dict
        """
        try:
            req = json.loads(request.get_data())
        except ValueError:
            return jsonify(
                {
                    u"roles": ScheduleRoles.roles,
                    u'selector': {
                        u"mac": ""
                    }
                }), 406

        registry.machine_schedule.create_schedule(req)
        cache.delete(request.path)
        return jsonify(req)

    @app.route('/scheduler/<string:role>', methods=['GET'])
    def get_schedule_by_role(role):
        """
        Scheduler
        List all the running schedules
        ---
        tags:
          - scheduler
        parameters:
          - name: role
            in: path
            description: name of the role
            required: true
            type: string
        responses:
          200:
            description: Current schedules for a given role
            schema:
                type: list
        """
        multi = role.split("&")
        data = registry.machine_schedule.get_machines_by_roles(*multi)
        return jsonify(data)

    @app.route('/scheduler/available', methods=['GET'])
    def get_available_machine():
        """
        Scheduler
        List all the machine without schedule
        ---
        tags:
          - scheduler
        responses:
          200:
            description: Current machine available for a schedule
            schema:
                type: list
        """
        data = registry.machine_schedule.get_available_machines()
        return jsonify(data)

    @app.route('/scheduler/ip-list/<string:role>', methods=['GET'])
    def get_schedule_role_ip_list(role):
        """
        Scheduler
        List all the IP addresses of a given schedules role
        ---
        tags:
          - scheduler
        parameters:
          - name: role
            in: path
            description: name of the role
            required: true
            type: string
        responses:
          200:
            description: Current IP address of schedules for a given role
            schema:
                type: list
        """
        ip_list_role = registry.machine_schedule.get_role_ip_list(role)

        return jsonify(ip_list_role)

    @app.route("/shutdown", methods=["POST"])
    def shutdown():
        """
        Shutdown
        Shutdown the application
        ---
        tags:
          - ops
        responses:
          200:
            description: List of the state of each PIDs
        """
        return ops.shutdown(ec)

    @app.route("/sync-notify", methods=["POST"])
    def sync_notify():
        """
        Sync process notify POST to this route to tell everything is synced for matchbox
        ---
        tags:
          - matchbox
        responses:
          200:
            description: Notify received
            schema:
                type: dict
        """
        ts = time.time()
        cache.set("sync-notify", ts, timeout=ec.sync_notify_ttl)
        return jsonify({"ts": ts, "ttl": ec.sync_notify_ttl}), 200

    @app.route("/sync-notify", methods=["GET"])
    def sync_notify_status():
        """
        Sync process notify POST to this route to tell everything is synced for matchbox
        ---
        tags:
          - matchbox
        responses:
          200:
            description: Notify received
            schema:
                type: dict
        """
        sync = cache.get("sync-notify")
        if sync:
            return jsonify({"sync-notify": sync}), 200

        app.logger.warning("sync-notify is None")
        return jsonify({"sync-notify": False}), 503

    @app.route('/ui', methods=['GET'])
    def user_interface():
        return render_template('index.html')

    @app.route('/ui/view/machine', methods=['GET'])
    def user_view_machine():
        res = jsonify(registry.user_interface.get_machines_overview())
        resp = make_response(res)
        resp.headers['Access-Control-Allow-Origin'] = '*'

        return resp

    @app.route('/ui/view/states', methods=['GET'])
    def user_view_machine_statuses():
        data_since_last_min = request.args.get('data_since_last_min') if request.args.get('data_since_last_min') else 30
        res = jsonify(registry.machine_state.fetch(finished_in_less_than_min=int(data_since_last_min)))
        resp = make_response(res)
        resp.headers['Access-Control-Allow-Origin'] = '*'

        return resp
