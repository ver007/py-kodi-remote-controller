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
BUFFER_SIZE = 1024
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
            action="count",
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
    data = ''
    while True:
        filler = s.recv(BUFFER_SIZE)
        logging.debug('data received: %s', filler)
        logging.debug('length of the filler: %i', len(filler))
        data += filler
        nb_open_brackets = data.count('{') - data.count('}')
        logging.debug('number of open brackets: %i', nb_open_brackets)
        if nb_open_brackets == 0:
            break
        else:
            logging.info('api reception incomplete')
    s.close()
    logging.debug('data length: %i', len(data))
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
    print "Loading the XBMC server library, this may be very long"
    nb_albums = get_nb_albums(obj.xbmc_ip, obj.xbmc_port)
    logging.debug('number of albums: %i', nb_albums)
    obj.nb_albums = nb_albums
    limits = range(0, nb_albums, 10)
    if not limits[-1] == nb_albums:
        limits.append(nb_albums)
    for start, end in zip(limits[:-1], limits[1:]):
        logging.debug('Processing album %i to %i ...', start, end)
        while True:
            try:
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
                break
            except KeyError:
                logging.info('error when loading library, retry')
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

# other

def get_albums_search(search_string, obj):
    '''Internal album indexes for a string search'''
    search_result_title = []
    for i, album_title in enumerate(obj.albums_title):
        if search_string in album_title.lower():
            search_result_title.append(i)
    search_result_artist = []
    logging.debug('search result by title: %s', search_result_title)
    for i, album_artist in enumerate(obj.albums_artist):
        if search_string in album_artist[0].lower():
            search_result_artist.append(i)
    logging.debug('search result by artist: %s', search_result_artist)
    return sorted(list(set(search_result_title + search_result_artist)))

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
    tracks = None
    try:
        tracks = ret['result']['items']
    except KeyError:
        pass
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
    item = None
    try:
        item = ret['result']['item']
    except KeyError:
        pass
    return item

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
    result = None
    try:
        result = ret['result']
    except KeyError:
        logging.debug('no properties found, player not active')
        pass
    return result

def system_friendly_name(ip, port):
    '''Get the system name and hostname'''
    command = {"jsonrpc": "2.0",
            "method": "XBMC.GetInfoLabels",
            "params": {
                "labels": ["System.FriendlyName"] },
            "id": 1}
    ret = call_api(ip, port, command)
    display_result(ret)
    return ret['result']['System.FriendlyName']

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

def set_player_stop(ip, port):
    '''Stops playback'''
    logging.debug('call function set_player_stop')
    command = {"jsonrpc": "2.0",
            "method": "Player.Stop",
            "params": {
                "playerid": 0 },
            "id": 1}
    ret = call_api(ip, port, command)
    display_result(ret)

# display function

def disp_albums_index(albums_pos, obj):
    '''Display albums list from internal index'''
    logging.debug('call disp_albums_index')
    print
    for i, album_pos in enumerate(albums_pos):
        print ("%02i. %s by %s (%s) [%i]") % (
                i + 1,
                obj.albums_title[album_pos],
                obj.albums_artist[album_pos][0],
                obj.albums_year[album_pos],
                obj.albums_id[album_pos] )
    print
    print "Total number of albums: %i" % obj.nb_albums
    print

def disp_playlist(properties, tracks):
    '''Display playlist'''
    if properties:
        position = properties['position']
    else:
        position = -1
    print
    if tracks:
        for i, track in enumerate(tracks):
            if i == position:
                print ">> ",
            else:
                print "   ",
            print "%02d. %s - %s" % (
                    track['track'],
                    track['artist'][0],
                    track['title'] )
    else:
        print "[playlist empty]"
    print

def disp_now_playing(item, properties):
    '''Display the now playing part of display_what'''
    print
    if item:
        disp_rating = '.....'
        for i in range(item['rating']):
            disp_rating[i] = '*'
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
    else:
        print "[not playing anything]"

def disp_next_playing(properties, items):
    '''Display the next playing part of display_what'''
    print
    if properties:
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
        if verbosity == 2:
            logging.basicConfig(level=logging.DEBUG)
        elif verbosity == 1:
            logging.basicConfig(level=logging.INFO)
        logging.info('XBMC controller started in verbosity mode ...')
        logging.debug('... and even in high verbosity mode!')
        # initialize library description
        self.nb_albums = 0
        self.albums_id = []
        self.albums_title = []
        self.albums_artist = []
        self.albums_year = []
        # fill data
        get_audio_library(self)
        # customize prompt
        sys_name = system_friendly_name(self.xbmc_ip, self.xbmc_port)
        self.prompt = "(" + sys_name + ") "
        # welcome message
        print "For a quick start, try play_album"
        print

    # albums functions

    def do_albums_random(self, line):
        '''
        Display a random selection of albums
        Usage: albums_random
        '''
        logging.debug('call function do_albums_random')
        albums_pos = random.sample(xrange(self.nb_albums), DISPLAY_NB_LINES)
        disp_albums_index(albums_pos, self)

    def do_albums_page(self, line):
        '''
        Display a given page of the albums library
        Usage: albums_page [page]
            The page is optional, a random page is displayed without it.
        '''
        logging.debug('call function do_albums_page')
        page_nb = parse_single_int(line)
        if not page_nb:
            logging.info('no page number provided')
            page_nb = random.randrange(int(self.nb_albums / 10) + 1)
        albums_pos = range(
                (page_nb - 1)  * DISPLAY_NB_LINES, 
                page_nb * DISPLAY_NB_LINES )
        disp_albums_index(albums_pos, self)

    def do_albums_recent(self, line):
        '''
        Display recently added albums
        Usage: albums_recent
        '''
        logging.debug('call function do_albums_recent')
        albums_pos = range(
                self.nb_albums - DISPLAY_NB_LINES, 
                self.nb_albums)
        disp_albums_index(albums_pos, self)

    def do_albums_search(self, line):
        '''
        Search into the albums
        Usage: albums_search string
            List all albums containing the string in the title or artist.
        '''
        logging.debug('call function do_albums_search')
        search_string = line.lower()
        albums_pos = get_albums_search(search_string, self)
        disp_albums_index(albums_pos, self)

    # playlist functions

    def do_playlist_show(self, line):
        '''
        Show the current audio playlist
        Usage: playlist_show
        '''
        logging.debug('call function do_playlist_show')
        properties = get_properties(self.xbmc_ip, self.xbmc_port)
        tracks = playlist_get_items(self.xbmc_ip, self.xbmc_port)
        disp_playlist(properties, tracks)

    def do_playlist_add(self, line):
        '''
        Add an album to the playlist
        Usage: playlist_add [id]
            Add the album id to the current playlist.
            Use the albums function to find the id.
            The id is optional, an album is randomly selected without it.
        '''
        logging.debug('call function do_playlist_add')
        album_id = parse_single_int(line)
        if not album_id:
            logging.info('no album id provided')
            album_id = random.randrange(self.nb_albums)
            print "Album %i will be added to the playlist" % album_id
        set_playlist_add(album_id, self.xbmc_ip, self.xbmc_port)

    def do_playlist_clear(self, line):
        '''
        Clear the playlist
        Usage: playlist_clear
            Remove all items from the current playlist.
        '''
        logging.debug('call function do_playlist_clear')
        set_playlist_clear(self.xbmc_ip, self.xbmc_port)

    # play functions

    def do_play_album(self, line):
        '''
        Play a single album
        Usage: play_album [id]
            Play the album behind the id.
            Use the albums function to find the id.
            The id is optional, an album is randomly selected without it.
        '''
        logging.debug('call function do_play_album')
        album_id = parse_single_int(line)
        if not album_id:
            logging.info('no album id provided')
            album_id = random.randrange(self.nb_albums)
            print "Album %i will be played" % album_id
        set_playlist_clear(self.xbmc_ip, self.xbmc_port)
        set_playlist_add(album_id, self.xbmc_ip, self.xbmc_port)
        set_player_open(self.xbmc_ip, self.xbmc_port)

    def do_play_party(self, line):
        '''
        Start a big party!
        Usage: play_party
        '''
        logging.debug('call function do_play_party')
        # set_player_open(self.xbmc_ip, self.xbmc_port)

    def do_play_pause(self, line):
        '''
        Switch to play or pause
        Usage: play_pause
            Switch to pause if playing, switch to play if in pause.
        '''
        logging.debug('call function do_play_pause')
        set_player_play_pause(self.xbmc_ip, self.xbmc_port)

    def do_play_stop(self, line):
        '''
        Stop the music
        Usage: play_stop
            Stop the music and go home, I repeat, stop the music and go home.
        '''
        logging.debug('call function do_play_stop')
        set_player_stop(self.xbmc_ip, self.xbmc_port)

    def do_play_what(self, line):
        '''
        Detail status of what is currently played
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
