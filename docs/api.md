# Enjoliver API

Everything has to go through this endpoint.

This is the available routes:

    [
      "/",
      "/apidocs/",
      "/apidocs/index.html",
      "/apispec_1.json",
      "/assets",
      "/assets/<path:path>",
      "/backup/db",
      "/backup/export",
      "/boot.ipxe",
      "/boot.ipxe.0",
      "/config",
      "/configs",
      "/discovery",
      "/discovery/ignition-journal",
      "/discovery/ignition-journal/<string:uuid>",
      "/discovery/ignition-journal/<string:uuid>/<string:boot_id>",
      "/discovery/interfaces",
      "/flasgger_static/<path:filename>",
      "/healthz",
      "/ignition",
      "/ignition-pxe",
      "/ignition/version",
      "/ignition/version/<string:filename>",
      "/install-authorization/<string:request_raw_query>",
      "/ipxe",
      "/lifecycle/coreos-install",
      "/lifecycle/coreos-install/<string:status>/<string:request_raw_query>",
      "/lifecycle/ignition",
      "/lifecycle/ignition/<string:request_raw_query>",
      "/lifecycle/rolling",
      "/lifecycle/rolling/<string:request_raw_query>",
      "/metadata",
      "/metrics",
      "/scheduler",
      "/scheduler/<string:role>",
      "/scheduler/available",
      "/scheduler/ip-list/<string:role>",
      "/shutdown",
      "/static/<path:filename>",
      "/sync-notify",
      "/ui",
      "/ui/view/machine",
      "/ui/view/states"
    ]

A Swagger UI is available at `/apidocs/index.html`

![swagger](docs/swagger.png)

The Enjoliver API is backed by a SQL database.

![sql](docs/sql.jpg)



## Sync

Matchbox store his state inside filesystem folders (JSON).

To keep it up-to-date, the sync process query the Enjoliver API `/scheduler/...`

In this current topology, the matchbox state isn't critical and can be regenerated at any time.



## Scheduler

By querying the Enjoliver API `/scheduler/available`, the scheduler can affect discovery instances to a role.


