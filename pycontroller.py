#!/usr/bin/env python
#
# Copyright 2013 Arn-O. See the LICENSE file at the top-level directory of this
# distribution and at
# https://github.com/Arn-O/py-xbmc-remote-controller/blob/master/LICENSE.

'''
XBMC remote controller based on TCP transport, JSON and using the (cmd) interface.
'''

import socket
import json
import cmd
import argparse

# global constants
BUFFER_SIZE = 1024
DISPLAY_NB_LINES = 20

# utilities functions

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

def display_result(ret):
    '''Display command result for simple methods'''
    if ret['result'] == 'OK':
        print 'Command processed successfully'
    else:
        print 'Too bad, something went wrong'

# parsers
def parse_get_albums(line):
    '''Parse line and return start/end for get_albums'''
    if len(line) == 0:
        start = 0
    else:
        start = int(line)
    end = start + DISPLAY_NB_LINES
    return (start, end)

# process return messages

class XBMCRemote(cmd.Cmd):
        
    '''Subclass of the cmd class'''
    
    def preloop(self):
        '''Override and used for class variable'''
        (self.xbmc_ip, self.xbmc_port) = get_xbmc_params()

    def do_audio_library(self, line):
        '''
        Set of namespace AudioLibrary methods.
        '''
        print 'Try help audio_library'

    def do_audio_library_get_albums(self, line):
        '''
        Retrieve all albums with criteria.
        Usage: audio_library_get_albums [start]
        '''
        (start, end) = parse_get_albums(line)
        command = {"jsonrpc": "2.0",
                "method": "AudioLibrary.GetAlbums",
                "params": { "limits": { "start": start, "end": end } },
                "id": 1}
        ret = call_api(self.xbmc_ip, self.xbmc_port, command)
        albums = ret['result']['albums']
        for album in albums:
            print ('Album ID: %4i - %s' % (album['albumid'], album['label']))

    def do_audio_library_scan(self, line):
        '''
        Scan the audio library.
        Usage: audio_library_scan
        '''
        command = {"jsonrpc": "2.0",
                "method": "AudioLibrary.Scan",
                "id": 1}
        ret = call_api(self.xbmc_ip, self.xbmc_port, command)
        display_result(ret)

    def do_gui(self, line):
        '''
        Set of namespace GUI methods.
        '''
        print 'Try help gui'

    def do_gui_show_notification(self, line):
        '''
        Show a GUI notification with the text 'message' in the low right corner.
        Usage: gui_show_notification message
        '''
        command = {"jsonrpc": "2.0",
                "method": "GUI.ShowNotification",
                "params": {"title": "PyController", "message":line},
                "id": 1}
        ret = call_api(self.xbmc_ip, self.xbmc_port, command)
        display_result(ret)
        
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
        command = {"jsonrpc": "2.0",
                "method": "JSONRPC.Version",
                "id": 1}
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
        command = {"jsonrpc": "2.0",
                "method": "Player.GetActivePlayers",
                "id": 1}
        ret = call_api(self.xbmc_ip, self.xbmc_port, command)
        if len(ret['result']) == 0:
            print 'Currently no active player'
        else:
            if len(ret['result']) == 1:
                print 'One active player: ' + ret['result'][0]['type']
            else:
                # if two player, it can only be audio and picture
                print 'Two active players: audio and picture'

    def do_system(self, line):
        '''
        Set of namespace system methods.
        '''
        print 'Try help system'

    def do_system_reboot(self, line):
        '''
        Reboot the XBMC server.
        Usage: system_reboot
        '''
        command = {"jsonrpc": "2.0",
                "method": "System.Reboot",
                "id": 1}
        ret = call_api(self.xbmc_ip, self.xbmc_port, command)
        display_result(ret)

    def do_EOF(self, line):
        '''Override end of file'''
        print "Bye!"
        return True

def main():
    '''Where everything starts'''

    remote_controller = XBMCRemote()
    remote_controller.cmdloop()

if __name__ == '__main__':
    main()
