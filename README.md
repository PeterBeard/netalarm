netalarm
========

A cron-like alarm system that communicates over TCP.

How It Works
============

* The netalarm server watches the ```netalarm``` file for alarm definitions that follow crontab syntax (see the included ```netalarm``` file for details)
* Clients tell the server the names of the alarms they want to be alerted about
* The server then sends a signal to any subscribed clients when an alarm is triggered
* Clients perform the action defined in ```netalarm-client``` when they receive an appropriate trigger message from the server (example in included ```netalarm-client``` file)

Installation
============

Server
------
* Add some alarm definitions to the ```netalarm``` file
* Run the server in the background with ```python server.py&```
  * Use ```screen``` or ```tmux``` if you want to close the terminal containing the server process

Client
------
* Add some alarm definitions to the ```netalarm-client``` file
* Make sure the server is running so that the client can subscribe to its alarms
* Run the client in the background with ```python testclient.py&```
  * Use ```screen``` or ```tmux``` if you want to close the terminal containing the client process
