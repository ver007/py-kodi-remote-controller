#!/usr/bin/env python
#
# Copyright 2013 Arn-O. See the LICENSE file at the top-level directory of this
# distribution and at
# https://github.com/Arn-O/py-xbmc-remote-controller/blob/master/LICENSE.

'''
XBMC remote controller based on TCP transport and JSON and using the (cmd) interface.
'''

import socket
import json

# global constants
XBMC_IP = '192.168.1.65'
XBMC_PORT = 9090
BUFFER_SIZE = 1024

def main():
    '''Where everything starts.'''
    command = {'jsonrpc': '2.0', 'method': 'Player.GetActivePlayers', 'id': 1}
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((XBMC_IP, XBMC_PORT))
    s.send(json.dumps(command))
    data = s.recv(BUFFER_SIZE)
    s.close()
    print data

if __name__ == '__main__':
    main()
