#!/usr/bin/env python
#
# Copyright 2014 Arn-O. See the LICENSE file at the top-level directory of this
# distribution and at
# https://github.com/Arn-O/py-xbmc-remote-controller/blob/master/LICENSE.

'''
XBMC remote controller based on TCP transport, JSON and using the (cmd) interface.
'''

import socket
import json
from datetime import timedelta
import pickle
import random
import cmd
import logging
import argparse

# global constants
BUFFER_SIZE = 2048
DISPLAY_NB_LINES = 10

# utility functions

def get_pyxbmc_params():
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

# API call management

def call_api(ip, port, command):
    '''Send the command using TCP'''
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, port))
    logging.debug('command: %s', command)
    s.send(json.dumps(command))
    data = s.recv(BUFFER_SIZE)
    s.close()
    logging.debug('data length: %i', len(data))
    if len(data) == BUFFER_SIZE:
        logging.warning('return is the size of the buffer')
    ret = json.loads(data)
    logging.debug('return: %s', ret)
    return ret

def display_result(ret):
    '''Display command result for simple methods'''
    logging.debug('call display_result')
    if 'error' in ret:
        logging.error('too bad, something went wrong')
    else:
        logging.info('command processed successfully')

def is_file(fname):
    '''Return false if the file does not exist'''
    logging.debug('call function is_file')
    try:
        open(fname)
    except IOError:
        return False
    return True

# local files

def is_library_files():
    '''Check if there are library local files'''
    logging.debug('call function is_library_files')
    ret = True
    ret = ret and is_file('albums_id.pickle')
    ret = ret and is_file('albums_title.pickle')
    ret = ret and is_file('albums_artist.pickle')
    ret = ret and is_file('albums_year.pickle')
    logging.debug('library files check: %s', ret)
    return ret

def get_audio_library(obj):
    '''Manage lists for audio library, from a local file or the server'''
    logging.debug('call function get_audio_library')
    logging.debug('load albums library in memory')
    if is_library_files():
        get_audio_library_from_files(obj)
    else:
        get_audio_library_from_server(obj)

def get_audio_library_from_files(obj):
    '''Load the library in memory from local files'''
    logging.debug('call function get_audio_library_from_files')
    f = open('albums_id.pickle', 'rb')
    obj.albums_id = pickle.load(f)
    f.close()
    f = open('albums_title.pickle', 'rb')
    obj.albums_title = pickle.load(f)
    f.close()
    f = open('albums_artist.pickle', 'rb')
    obj.albums_artist = pickle.load(f)
    f.close()
    f = open('albums_year.pickle', 'rb')
    obj.albums_year = pickle.load(f)
    f.close()
    obj.nb_albums = len(obj.albums_id)

def get_audio_library_from_server(obj):
    '''Load the library in memory from the XBMC server'''
    logging.debug('get_audio_library_from_server')
    nb_albums = get_nb_albums(obj.xbmc_ip, obj.xbmc_port)
    obj.nb_albums = nb_albums
    limits = range(0, nb_albums, 10)
    if not limits[-1] == nb_albums:
        limits.append(nb_albums)
    for start, end in zip(limits[:-1], limits[1:]):
        print 'Processing album %i to %i ...' % (start, end)
        command = {"jsonrpc": "2.0",
                "method": "AudioLibrary.GetAlbums",
                "params": {
                    "properties": ["title", "artist", "year"],
                    "limits": { "start": start, "end": end } },
                "id": 1}
        ret = call_api(obj.xbmc_ip, obj.xbmc_port, command)
        for album in ret['result']['albums']:
            obj.albums_id.append(album['albumid'])
            obj.albums_title.append(album['title'])
            obj.albums_artist.append(album['artist'])
            obj.albums_year.append(album['year'])
    f = open('albums_id.pickle', 'wb')
    pickle.dump(obj.albums_id, f)
    f.close()
    f = open('albums_title.pickle', 'wb')
    pickle.dump(obj.albums_title, f)
    f.close()
    f = open('albums_artist.pickle', 'wb')
    pickle.dump(obj.albums_artist, f)
    f.close()
    f = open('albums_year.pickle', 'wb')
    pickle.dump(obj.albums_year, f)
    f.close()

# parsers

def parse_single_int(line):
    '''Parse line for a single int'''
    logging.debug('call function parse_single_int')
    args = str.split(line)
    ret_val = None
    #TODO: catch error instead of test
    if len(args) == 1:
        ret_val = int(args[0])
    return ret_val

def parse_get_int(line):
    '''Parse line for an integer'''
    if len(line) == 0:
        ret_val = 0
    else:
        ret_val = int(line)
    return ret_val

def parse_get_limits(line):
    '''Parse line and return start/end limits'''
    if len(line) == 0:
        start = 0
    else:
        start = int(line)
    end = start + DISPLAY_NB_LINES
    return (start, end)

def parse_get_string(line):
    '''Parse line and return the first string (without space)'''
    args = str.split(line)
    return args[0]

# getters

def playlist_get_items(ip, port):
    '''Get all items from the audio playlist'''
    logging.debug('call get_playlist_get_items')
    command = {"jsonrpc": "2.0",
            "method": "Playlist.GetItems",
            "params": {
                "playlistid": 0,
                "properties": ["title", "artist", "duration", "track"] },
            "id": 1}
    ret = call_api(ip, port, command)
    display_result(ret)
    tracks = ret['result']['items']
    return tracks

def get_item(ip, port):
    '''Get the current played item'''
    logging.debug('call function get_item')
    command = {"jsonrpc": "2.0",
            "method": "Player.GetItem",
            "params": {
                "playerid": 0,
                "properties": [
                    "album",
                    "title",
                    "artist",
                    "year",
                    "rating" ] },
            "id": 1}
    ret = call_api(ip, port, command)
    display_result(ret)
    return ret['result']['item']

def get_properties(ip, port):
    '''Get properties of the played item'''
    logging.debug('call function get_properties')
    command = {"jsonrpc": "2.0",
            "method": "Player.GetProperties",
            "params": {
                "playerid": 0,
                "properties": [
                    "time",
                    "totaltime",
                    "percentage",
                    "position" ] },
            "id": 1}
    ret = call_api(ip, port, command)
    display_result(ret)
    return ret['result']

def get_nb_albums(ip, port):
    '''Give the total number of albums in the library'''
    command = {"jsonrpc": "2.0",
            "method": "AudioLibrary.GetAlbums",
            "params": {
                "limits": { "start": 0, "end": 1 } },
            "id": 1}
    ret = call_api(ip, port, command)
    display_result(ret)
    return ret['result']['limits']['total']

# setters

def set_playlist_clear(ip, port):
    '''Clear the audio playlist'''
    logging.debug('call function set_playlist_clear')
    command = {"jsonrpc": "2.0",
            "method": "Playlist.Clear",
            "params": {"playlistid": 0 },
            "id": 1}
    ret = call_api(ip, port, command)
    display_result(ret)

def set_playlist_add(album_id, ip, port):
    '''Add an album to the audio playlist'''
    logging.debug('call function set_playlist_add')
    command = {"jsonrpc": "2.0",
            "method": "Playlist.Add",
            "params": {
                "playlistid": 0,
                "item": {"albumid": album_id } },
            "id": 1}
    ret = call_api(ip, port, command)
    display_result(ret)

def set_player_open(ip, port):
    '''Open the audio playlist'''
    logging.debug('call function set_player_open')
    command = {"jsonrpc": "2.0",
            "method": "Player.Open",
            "params": {
                "item": {"playlistid": 0 } },
            "id": 1}
    ret = call_api(ip, port, command)
    display_result(ret)

def set_player_play_pause(ip, port):
    '''Pauses or unpause playback and returns the new state'''
    logging.debug('call function set_player_play_pause')
    command = {"jsonrpc": "2.0",
            "method": "Player.PlayPause",
            "params": {
                "playerid": 0 },
            "id": 1}
    ret = call_api(ip, port, command)
    display_result(ret)

# display function

def disp_album_info(pos, album):
    '''Display album info in line'''
    logging.debug('call disp_album_info')
    print ('%i. %s by %s (%s) - id: %i') % (
            pos,
            album['title'],
            album['artist'][0],
            album['year'],
            album['albumid'])

def disp_now_playing(item, properties):
    '''Display the now playing part of display_what'''
    disp_rating = '.....'
    for i in range(item['rating']):
        disp_rating[i] = '*'
    print
    print 'Now Playing:'
    print
    print "%s - %s (%s)" % (item['artist'][0], item['album'], item['year'])
    print "   %s - [%s]" % (item['title'], disp_rating)
    print "   %02d:%02d:%02d / %02d:%02d:%02d - %i %%" % (
            properties['time']['hours'],
            properties['time']['minutes'],
            properties['time']['seconds'],
            properties['totaltime']['hours'],
            properties['totaltime']['minutes'],
            properties['totaltime']['seconds'],
            properties['percentage'] )

def disp_next_playing(properties, items):
    '''Display the next playing part of display_what'''
    print
    print "(%i / %i) - Next: %s - %s" % (
            properties['position'] + 1, 
            len(items),
            items[properties['position'] + 1]['artist'][0],
            items[properties['position'] + 1]['title'] )
    print

# process return messages

class XBMCRemote(cmd.Cmd):
        
    '''Subclass of the cmd class'''
    
    def preloop(self):
        '''Override and used for class variable'''
        (self.xbmc_ip, self.xbmc_port, verbosity) = get_pyxbmc_params()
        if verbosity:
            logging.basicConfig(level=logging.DEBUG)
        logging.info('XBMC controller started in verbosity mode')
        # initialize library description
        self.nb_albums = 0
        self.albums_id = []
        self.albums_title = []
        self.albums_artist = []
        self.albums_year = []
        # fill data
        get_audio_library(self)

    # albums functions

    def do_albums_random(self, line):
        '''
        Display a random selection of albums.
        Usage: albums_random
        '''
        logging.debug('call function do_albums_random')
        albums_pos = random.sample(xrange(self.nb_albums), DISPLAY_NB_LINES)
        print
        for i, album_pos in enumerate(albums_pos):
            album = {}
            album['albumid'] = self.albums_id[album_pos]
            album['title'] = self.albums_title[album_pos]
            album['artist'] = self.albums_artist[album_pos]
            album['year'] = self.albums_year[album_pos]
            disp_album_info(i, album)            
        print
        print 'Total number of albums: %i' % self.nb_albums
        print

    # playlist functions

    def do_playlist_show(self, line):
        '''
        Show the current audio playlist
        Usage: playlist_show
        '''
        logging.debug('call function do_playlist_show')
        tracks = playlist_get_items(self.xbmc_ip, self.xbmc_port)

    # play functions

    def do_play_album(self, line):
        '''
        Play a single album.  
        Usage: play_album [id]
            Play the album behind the id.
            Use the albums function to find the id.
            The id is optional, an album is randomly selected without it.
        '''
        logging.debug('call function do_play_album')
        album_id = parse_single_int(line)
        if not album_id:
            logging.info('no album id provided')
            album_id = 0
        set_playlist_clear(self.xbmc_ip, self.xbmc_port)
        set_playlist_add(album_id, self.xbmc_ip, self.xbmc_port)
        set_player_open(self.xbmc_ip, self.xbmc_port)

    def do_play_pause(self, line):
        '''
        Switch to play or pause.  
        Usage: play_pause
            Switch to pause if playing, switch to play if in pause.
        '''
        logging.debug('call function do_play_pause')
        set_player_play_pause(self.xbmc_ip, self.xbmc_port)

    def do_play_what(self, line):
        '''
        Detail status of what is currently played.
        Usage: play_what
        '''
        logging.debug('call function do_play_what')
        item = get_item(self.xbmc_ip, self.xbmc_port)
        properties = get_properties(self.xbmc_ip, self.xbmc_port)
        items = playlist_get_items(self.xbmc_ip, self.xbmc_port)
        disp_now_playing(item, properties)
        disp_next_playing(properties, items)

    def do_EOF(self, line):
        '''Override end of file'''
        logging.info('Bye!')
        print 'Bye!'
        return True

def main():
    '''Where everything starts'''

    remote_controller = XBMCRemote()
    remote_controller.cmdloop()

if __name__ == '__main__':
    main()
