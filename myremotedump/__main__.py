#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# Author: Massimiliano Torromeo <massimiliano.torromeo@gmail.com>
# License: BSD
#
from __future__ import print_function

name = "myremotedump"
description = "Dumps a firewalled MySQL database via a ssh tunnel to the remote system"
version = "0.1.0"
url = "http://github.com/mtorromeo/myremotedump"

import re
import os
import sys
import SocketServer

from threading import Thread

try:
    import Crypto.Random as Random
except ImportError:
    Random = None


class ForwardServer(SocketServer.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


class Handler(SocketServer.BaseRequestHandler):
    def handle(self):
        try:
            chan = self.ssh_transport.open_channel('direct-tcpip', (self.chain_host, self.chain_port), self.request.getpeername())
        except Exception:
            return

        if chan is None:
            return

        import select
        while True:
            r, w, x = select.select([self.request, chan], [], [])
            if self.request in r:
                data = self.request.recv(1024)
                if len(data) == 0:
                    break
                chan.send(data)
            if chan in r:
                data = chan.recv(1024)
                if len(data) == 0:
                    break
                self.request.send(data)
        chan.close()
        self.request.close()


class TunnelThread(Thread):
    def __init__(self, ssh_server, local_port=0, ssh_port=22, remote_host="localhost", remote_port=None, username=None, password=None, compress=False):
        Thread.__init__(self)
        if Random:
            Random.atfork()
        if remote_port is None:
            remote_port = local_port
        self.local_port = local_port

        import paramiko
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.load_system_host_keys()
        self.ssh_client.set_missing_host_key_policy(paramiko.WarningPolicy())
        self.ssh_client.connect(ssh_server, ssh_port, username=username, password=password, look_for_keys=True, compress=compress)

        transport = self.ssh_client.get_transport()
        transport.set_keepalive(30)

        class SubHandler(Handler):
            chain_host = remote_host
            chain_port = remote_port
            ssh_transport = transport
        self.ffwd_server = ForwardServer(('', self.local_port), SubHandler)
        self.ip, self.local_port = self.ffwd_server.server_address

    def run(self):
        self.ffwd_server.serve_forever()

    def join(self):
        if self.ffwd_server is not None:
            self.ffwd_server.shutdown()
        self.ssh_client.close()
        del self.ffwd_server
        del self.ssh_client
        Thread.join(self)


def run(cmd):
    from subprocess import Popen, PIPE, STDOUT
    p = Popen(cmd, stdout=PIPE, stderr=STDOUT)

    while True:
        nextline = p.stdout.readline().decode('utf-8')
        if nextline == '' and p.poll() != None:
            break
        sys.stdout.write(nextline)
        sys.stdout.flush()

    p.communicate()
    return p.returncode


def main():
    import setproctitle
    import argparse
    import logging
    import getpass

    setproctitle.setproctitle(name)

    parser = argparse.ArgumentParser(prog=name, description=description, usage='%(prog)s [-h] [-V] [-H MYSQLHOST] [-P MYSQLPORT] [user@]host -- mysqldump options')

    parser.add_argument('-V', '--version', action='version', version="%(prog)s " + version)
    parser.add_argument('-H', '--host', dest='mysqlhost', help='MySQL host', default='localhost')
    parser.add_argument('-P', '--port', dest='mysqlport', help='MySQL port', type=int, default=3306)
    parser.add_argument('host', metavar='user@host', help='SSH username and host (username is optional)')
    parser.add_argument('dumpoptions', nargs='+', metavar='mysqldump options', help='Options passwd to the mysqldump process')

    args = parser.parse_args()

    m = re.match('(?:(?P<user>.*)@)?(?P<host>[^:]+)(?::(?P<port>[0-9]+))?', args.host)
    if not m:
        print('Invalid ssh options')
        sys.exit(1)

    user = m.group('user') if m.group('user') else getpass.getuser()
    port = m.group('port') if m.group('port') else 22

    tunnel = TunnelThread(username=user, ssh_server=m.group('host'), ssh_port=port, remote_host=args.mysqlhost, remote_port=args.mysqlport, compress=True)
    tunnel.start()

    mysqldump = ['mysqldump', '-q', '--allow-keywords', '--hex-blob', '--single-transaction', '-R', '--triggers', '--tz-utc', '-E', '-h', '127.0.0.1', '-P', str(tunnel.local_port)]
    mysqldump.extend(args.dumpoptions)

    ret = run(mysqldump)

    tunnel.join()

    sys.exit(ret)

if __name__ == '__main__':
    main()
