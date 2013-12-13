myremotedump
============

Dumps a firewalled MySQL database via a ssh tunnel to the remote system.

Help
----

::

	usage: myremotedump [-h] [-V] [-H MYSQLHOST] [-P MYSQLPORT] [user@]host -- mysqldump options

	Dumps a firewalled MySQL database via a ssh tunnel to the remote system

	positional arguments:
	  user@host             SSH username and host (username is optional)
	  mysqldump options     Options passwd to the mysqldump process

	optional arguments:
	  -h, --help            show this help message and exit
	  -V, --version         show program's version number and exit
	  -H MYSQLHOST, --host MYSQLHOST
	                        MySQL host
	  -P MYSQLPORT, --port MYSQLPORT
	                        MySQL port

LICENSE
-------
Copyright (c) 2013 Massimiliano Torromeo

myremotedump is free software released under the terms of the BSD license.

See the LICENSE file provided with the source distribution for full details.

Contacts
--------

* Massimiliano Torromeo <massimiliano.torromeo@gmail.com>