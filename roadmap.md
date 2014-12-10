Netalarm Roadmap
================

* Version 0.1
  * Working client-server communication (see protocol.md)
  * cron-like alarm configuration on server
  * Server sends recurring alarms to subscribed client(s)
* Version 0.2
  * Python client API (maybe something similar to Flask)
  * Configurable logging (amount and location)
  * Installation script (setup.py)
    * Server should install to /etc/netalarm/
    * Client should install to /etc/netalarm-client/
* Version 0.3
  * Server (and perhaps also client) authentication
  * Messages should be signed
  * Optional message encryption
    * Either client or server can require it
    * Probably TLS
* ...more versions...
* Version 1.0
  * Freeze APIs
  * Web interface for server (maybe a web client too)
  * Several example clients (email alert, SMS, shell script, Raspberry Pi something or other)
  * Daemonize server process
    * Should also include systemd service file and/or init script
  * Distribute binary packages
    * At least Debian and MSI, probably RPM too
    * Maybe something for OS X too if I can find a Mac to test on
