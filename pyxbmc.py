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
import logging
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
    parser.add_argument("-v", "--verbosity",
            action="store_true",
            help='Increase output verbosity')
    args = parser.parse_args()
    return args.ip, args.port, args.verbosity

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
    logging.debug('call display_result')
    if 'result' in ret:
        if ret['result'] == 'OK':
            print 'Command processed successfully'
        else:
            print 'Too bad, something went wrong'
    else:
        print 'Weird, can''t read the result'

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
        (self.xbmc_ip, self.xbmc_port, verbosity) = get_xbmc_params()
        if verbosity:
            logging.basicConfig(level=logging.DEBUG)
        logging.info('XBMC controller started in verbosity mode')

    def do_audio_library(self, line):
        '''
        Set of namespace AudioLibrary methods.
        '''
        logging.debug('call do_audio_library')
        print 'Try help audio_library'

    def do_audio_library_clean(self, line):
        '''
        Cleans the audio library from non-existent items
        Usage: audio_library_clean
        '''
        logging.debug('call do_audio_library_clean')
        command = {"jsonrpc": "2.0",
                "method": "AudioLibrary.Clean",
                "id": 1}
        logging.debug('command: %s', command)
        ret = call_api(self.xbmc_ip, self.xbmc_port, command)
        logging.debug('return: %s', ret)
        display_result(ret)

    def do_audio_library_get_album_details(self, line):
        '''
        Retrieve details about a specific album.
        Usage: audio_library_get_album_degtails album_id
        '''
        logging.debug('call do_audio_library_get_albums')
        album_id = int(line)
        command = {"jsonrpc": "2.0",
                "method": "AudioLibrary.GetAlbumDetails",
                "params": { "albumid": album_id},
                "id": 1}
        logging.debug('command: %s', command)
        ret = call_api(self.xbmc_ip, self.xbmc_port, command)
        logging.debug('return: %s', ret)

    def do_audio_library_get_albums(self, line):
        '''
        Retrieve all albums with criteria.
        Usage: audio_library_get_albums [start]
        '''
        logging.debug('call do_audio_library_get_albums')
        (start, end) = parse_get_albums(line)
        command = {"jsonrpc": "2.0",
                "method": "AudioLibrary.GetAlbums",
                "params": { "limits": { "start": start, "end": end } },
                "id": 1}
        logging.debug('command: %s', command)
        ret = call_api(self.xbmc_ip, self.xbmc_port, command)
        logging.debug('return: %s', ret)
        albums = ret['result']['albums']
        for album in albums:
            print ('Album ID: %4i - %s' % (album['albumid'], album['label']))

    def do_audio_library_scan(self, line):
        '''
        Scan the audio library.
        Usage: audio_library_scan
        '''
        logging.debug('call do_audio_library_scan')
        command = {"jsonrpc": "2.0",
                "method": "AudioLibrary.Scan",
                "id": 1}
        logging.debug('command: %s', command)
        ret = call_api(self.xbmc_ip, self.xbmc_port, command)
        logging.debug('return: %s', ret)
        display_result(ret)

    def do_input(self, line):
        '''
        Set of namespace Input methods.
        '''
        logging.debug('call do_input')
        print 'Try help input'

    def do_input_context_menu(self, line):
        '''
        Display context menu.
        Usage: input_context_menu
        '''
        logging.debug('call do_input_context_menu')
        command = {"jsonrpc": "2.0",
                "method": "Input.ContextMenu",
                "id": 1}
        logging.debug('command: %s', command)
        ret = call_api(self.xbmc_ip, self.xbmc_port, command)
        logging.debug('return: %s', ret)
        display_result(ret)
    
    def do_input_home(self, line):
        '''
        Go to home screnn.
        Usage: input_home
        '''
        logging.debug('call do_input_home')
        command = {"jsonrpc": "2.0",
                "method": "Input.Home",
                "id": 1}
        logging.debug('command: %s', command)
        ret = call_api(self.xbmc_ip, self.xbmc_port, command)
        logging.debug('return: %s', ret)
        display_result(ret)

    def do_gui(self, line):
        '''
        Set of namespace GUI methods.
        '''
        logging.debug('call do_gui')
        print 'Try help gui'

    def do_gui_show_notification(self, line):
        '''
        Show a GUI notification with the text 'message' in the low right corner.
        Usage: gui_show_notification message
        '''
        logging.debug('call do_gui_show_notification')
        command = {"jsonrpc": "2.0",
                "method": "GUI.ShowNotification",
                "params": {"title": "PyController", "message": line},
                "id": 1}
        logging.debug('command: %s', command)
        ret = call_api(self.xbmc_ip, self.xbmc_port, command)
        logging.debug('return: %s', ret)
        display_result(ret)
        
    def do_json(self, line):
        '''
        Set of namespace JSONRPC methods.
        '''
        logging.debug('call do_json')
        print 'Try help json'

    def do_json_version(self, line):
        '''
        Get the JSON-RPC protocol version.
        Usage: json_version
        '''
        logging.debug('call do_json_version')
        command = {"jsonrpc": "2.0",
                "method": "JSONRPC.Version",
                "id": 1}
        logging.debug('command: %s', command)
        ret = call_api(self.xbmc_ip, self.xbmc_port, command)
        logging.debug('return: %s', ret)
        print ('JSON-RPC protocol version: %i.%i patch %i' %
                (ret['result']['version']['major'],
                ret['result']['version']['minor'],
                ret['result']['version']['patch']))

    def do_player(self, line):
        '''
        Set of namespace Player methods.
        '''
        logging.debug('call do_player')
        print 'Try help player'

    def do_player_get_actives(self, line):
        '''
        Get the active players.
        Usage: player_get_active
        '''
        logging.debug('call do_player_get_actives')
        command = {"jsonrpc": "2.0",
                "method": "Player.GetActivePlayers",
                "id": 1}
        logging.debug('command: %s', command)
        ret = call_api(self.xbmc_ip, self.xbmc_port, command)
        logging.debug('return: %s', ret)
        if len(ret['result']) == 0:
            print 'Currently no active player'
        else:
            if len(ret['result']) == 1:
                print 'One active player: ' + ret['result'][0]['type']
            else:
                # if two player, it can only be audio and picture
                print 'Two active players: audio and picture'

    def do_playlist(self, line):
        '''
        Set of namespace Playlist  methods.
        '''
        logging.debug('call do_playlist')
        print 'Try help playlist'

    def do_playlist_get_items(self, line):
        '''
        Get all items from playlist.
        Usage: playlist_get_items id
        '''
        logging.debug('call playlist_get_items')
        playlist_id = int(line)
        command = {"jsonrpc": "2.0",
                "method": "Playlist.GetItems",
                "params": {"playlistid": playlist_id},
                "id": 1}
        logging.debug('command: %s', command)
        ret = call_api(self.xbmc_ip, self.xbmc_port, command)
        logging.debug('return: %s', ret)

    def do_playlist_get_playlists(self, line):
        '''
        Get the existing playlist.
        Usage: playlist_get_playlists
        '''
        logging.debug('call playlist_get_playlists')
        command = {"jsonrpc": "2.0",
                "method": "Playlist.GetPlaylists",
                "id": 1}
        logging.debug('command: %s', command)
        ret = call_api(self.xbmc_ip, self.xbmc_port, command)
        logging.debug('return: %s', ret)

    def do_playlist_get_properties(self, line):
        '''
        Get the values of the given properties.
        Usage: playlist_get_properties id
        '''
        logging.debug('call playlist_get_properties')
        playlist_id = int(line)
        command = {"jsonrpc": "2.0",
                "method": "Playlist.GetProperties",
                "params": {"playlistid": playlist_id},
                "id": 1}
        logging.debug('command: %s', command)
        ret = call_api(self.xbmc_ip, self.xbmc_port, command)
        logging.debug('return: %s', ret)

    def do_system(self, line):
        '''
        Set of namespace System methods.
        '''
        logging.debug('call do_system')
        print 'Try help system'

    def do_system_reboot(self, line):
        '''
        Reboot the XBMC server.
        Usage: system_reboot
        '''
        logging.debug('call do_system_reboot')
        command = {"jsonrpc": "2.0",
                "method": "System.Reboot",
                "id": 1}
        logging.debug('command: %s', command)
        ret = call_api(self.xbmc_ip, self.xbmc_port, command)
        logging.debug('return: %s', ret)
        display_result(ret)

    def do_video_library(self, line):
        '''
        Set of namespace VideoLibrary methods.
        '''
        logging.debug('call do_video_library')
        print 'Try help audio_library'

    def do_video_library_clean(self, line):
        '''
        Clean the video library.
        Usage: video_library_clean
        '''
        logging.debug('call do_video_library_clean')
        command = {"jsonrpc": "2.0",
                "method": "VideoLibrary.Clean",
                "id": 1}
        logging.debug('command: %s', command)
        ret = call_api(self.xbmc_ip, self.xbmc_port, command)
        logging.debug('return: %s', ret)
        display_result(ret)

    def do_video_library_scan(self, line):
        '''
        Scan the video library.
        Usage: video_library_scan
        '''
        logging.debug('call do_video_library_scan')
        command = {"jsonrpc": "2.0",
                "method": "VideoLibrary.Scan",
                "id": 1}
        logging.debug('command: %s', command)
        ret = call_api(self.xbmc_ip, self.xbmc_port, command)
        logging.debug('return: %s', ret)
        display_result(ret)

    def do_EOF(self, line):
        '''Override end of file'''
        logging.debug('Bye!')
        print 'Bye!'
        return True

def main():
    '''Where everything starts'''

    remote_controller = XBMCRemote()
    remote_controller.cmdloop()

if __name__ == '__main__':
    main()
