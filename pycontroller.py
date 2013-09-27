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
import cmd
import argparse

# global constants
BUFFER_SIZE = 1024

def get_xbmc_params():
    '''Get XBMC sever IP and port'''
    parser = argparse.ArgumentParser()
    parser.add_argument("ip",
            help='IP of your XBMC server')
    parser.add_argument("-p", "--port",
            type=int,
            default=9090,
            help='TCP port of the XBMC server')
    args = parser.parse_args()
    return args.ip, args.port

def call_api(ip, port, command):
    '''Send the command using TCP'''
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, port))
    s.send(json.dumps(command))
    data = s.recv(BUFFER_SIZE)
    s.close()
    return json.loads(data)

class XBMCRemote(cmd.Cmd):
        
    '''Subclass of the cmd class'''
    
    def preloop(self):
        '''Override and used for class variable'''
        (self.xbmc_ip, self.xbmc_port) = get_xbmc_params()

    def do_json(self, line):
        '''
        Set of namespace JSONRPC methods.
        '''
        print 'Try help json'

    def do_json_version(self, line):
        '''
        Get the JSON-RPC protocol version.
        Usage: json_version
        '''
        command = {'jsonrpc': '2.0',
                'method': 'JSONRPC.Version',
                'id': 1}
        ret = call_api(self.xbmc_ip, self.xbmc_port, command)
        print ('JSON-RPC protocol version: %i.%i patch %i' %
                (ret['result']['version']['major'],
                ret['result']['version']['minor'],
                ret['result']['version']['patch']))

    def do_player(self, line):
        '''
        Set of namespace player methods.
        '''
        print 'Try help player'

    def do_player_get_actives(self, line):
        '''
        Get the active players.
        Usage: player_get_active
        '''
        command = {'jsonrpc': '2.0',
                'method': 'Player.GetActivePlayers',
                'id': 1}
        ret = call_api(self.xbmc_ip, self.xbmc_port, command)
        print ret

    def do_EOF(self, line):
        '''Override end of file'''
        print "Bye!"
        return True

def main():
    '''Where everything starts.'''

    remote_controller = XBMCRemote()
    remote_controller.cmdloop()


if __name__ == '__main__':
    main()
