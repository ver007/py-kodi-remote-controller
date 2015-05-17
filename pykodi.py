#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2015 Arn-O. See the LICENSE file at the top-level directory of this
# distribution and at
# https://github.com/Arn-O/py-kodi-remote-controller/blob/master/LICENSE.

'''
Kodi remote controller based on HTTP/TCP transport, JSON and using the (cmd) interface.
'''

import kodi_api
import en_api
import fancy_disp

import socket
import requests
import json
#from datetime import timedelta
from progressbar import *
import pickle
import time
import random
import cmd
import logging
import argparse
from sys import exit

# global constants
BUFFER_SIZE = 1024
DISPLAY_NB_LINES = 10
PROFILE_NAME = 'Kodi library'
ALBUM = 'albumid'
SONG = 'songid'

#TODO: add instrospect
#TODO: display number of transactions calls in echonest API

# utility functions

def get_pykodi_params():
    '''Get Kodi sever IP and port'''
    parser = argparse.ArgumentParser()
    parser.add_argument("ip",
            help='IP of your Kodi server')
    parser.add_argument("--tcp",
            action="store_true",
            help='Use TCP transport')
    parser.add_argument("-p", "--port",
            type=int,
            default=9090,
            help='TCP or HTTP port of the Kodi server')
    parser.add_argument("-u", "--user",
            help='User for HTTP transport')
    parser.add_argument("-pw", "--password",
            help='Password for HTTP transport')
    parser.add_argument("-v", "--verbosity",
            action="count",
            help='Increase output verbosity')
    parser.add_argument("-enk", "--echonest-key",
            help='Echonest API key')
    parser.add_argument("-c", "--command",
            default=0,
            help='Execute command and quit.')
    args = parser.parse_args()
    server_params = {}
    server_params['tcp'] = args.tcp
    server_params['ip'] = args.ip
    server_params['port'] = args.port
    server_params['user'] = args.user
    server_params['password'] = args.password
    if args.verbosity == 2:
        logging.basicConfig(level=logging.DEBUG)
    else:
        if args.verbosity == 1:
            logging.basicConfig(level=logging.INFO)
    logging.info('Kodi controller started in verbosity mode ...')
    logging.debug('... and even in high verbosity mode!')
    return server_params, args.echonest_key, args.command

# local files

def is_file(fname):
    '''Return false if the file does not exist'''
    logging.debug('call function is_file')
    try:
        open(fname)
    except IOError:
        return False
    return True

def is_library_files():
    '''Check if there are library local files'''
    logging.debug('call function is_library_files')
    ret = True
    ret = ret and is_file('albums.pickle')
    ret = ret and is_file('songs.pickle')
    logging.info('library files check: %s', ret)
    return ret

def get_audio_library(obj):
    '''Manage lists for audio library, from a local file or the server'''
    logging.debug('call function get_audio_library')
    logging.debug('load albums library in memory')
    if is_library_files():
        get_audio_library_from_files(obj)
    else:
        get_audio_library_from_server(obj)

def save_songs(songs):
    '''Save songs to local files'''
    logging.debug('call function save_songs')
    f = open('songs.pickle', 'wb')
    pickle.dump(songs, f)
    f.close()

def save_albums(albums):
    '''Save albums to local files'''
    logging.debug('call function save_albums')
    f = open('albums.pickle', 'wb')
    pickle.dump(albums, f)
    f.close()

def get_audio_library_from_files(obj):
    '''Load the library in memory from local files'''
    logging.debug('call function get_audio_library_from_files')
    f = open('songs.pickle', 'rb')
    obj.songs = pickle.load(f)
    f.close()
    obj.nb_songs = len(obj.songs)
    f = open('albums.pickle', 'rb')
    obj.albums = pickle.load(f)
    f.close()
    obj.nb_albums = len(obj.albums)

def get_audio_library_from_server(obj):
    '''Load the library in memory from the Kodi server'''
    logging.debug('get_audio_library_from_server')
    print "Loading the Kodi server library, this may be very long"
    print
    # Loading songs
    songs_dummy = kodi_api.audiolibrary_get_songs(obj.kodi_params, 0, 1)
    nb_songs = songs_dummy['limits']['total']
    logging.debug('number of songs: %i', nb_songs)
    obj.nb_songs = nb_songs
    widgets = [
        'Songs: ', Percentage(),
        ' ', Bar(marker='#',left='[',right=']'),
        ' (', Counter(), ' in ' + str(nb_songs) + ') ',
        ETA()]
    pbar = ProgressBar(widgets=widgets, maxval=nb_songs)
    pbar.start()
    limits = range(0, nb_songs, 20)
    if not limits[-1] == nb_songs:
        limits.append(nb_songs)
    for start, end in zip(limits[:-1], limits[1:]):
        logging.info('Processing song %i to %i ...', start, end)
        pbar.update(start)
        while True:
            try:
                #TODO: use an API function
                command = {"jsonrpc": "2.0",
                        "method": "AudioLibrary.GetSongs",
                         "params": {
                            "properties": [
                                "title", 
                                "artist", 
                                "year",
                                "rating",
                                "playcount",
                                "musicbrainztrackid"
                                ],
                            "limits": { 
                                "start": start, 
                                "end": end } },
                        "id": 1}
                ret = kodi_api.call_api(obj.kodi_params, command)
                for song in ret['result']['songs']:
                    obj.songs[song['songid']] = {}
                    obj.songs[song['songid']]['title'] = song['title']
                    if song['artist']:
                        obj.songs[song['songid']]['artist'] = song['artist'][0]
                    obj.songs[song['songid']]['year'] = song['year']
                    obj.songs[song['songid']]['rating'] = song['rating']
                    obj.songs[song['songid']]['playcount'] = song['playcount']
                    obj.songs[song['songid']][
                            'musicbrainztrackid'] = song['musicbrainztrackid']
                    # store the last update to echonest profile
                    obj.songs[song['songid']]['rating_en'] = 0
                    obj.songs[song['songid']]['playcount_en'] = 0
                break
            except KeyError:
                #TODO: improve error catching, limit to API errors
                logging.info('error when loading library, retry')
    pbar.finish()
    save_songs(obj.songs)
    # Loading albums
    albums_dummy = kodi_api.audiolibrary_get_albums(obj.kodi_params, 0, 1)
    nb_albums = albums_dummy['limits']['total']
    logging.debug('number of albums: %i', nb_albums)
    obj.nb_albums = nb_albums
    widgets = [
        'Albums: ', Percentage(),
        ' ', Bar(marker='#',left='[',right=']'),
        ' (', Counter(), ' in ' + str(nb_albums) + ') ',
        ETA()]
    pbar = ProgressBar(widgets=widgets, maxval=nb_albums)
    pbar.start()
    limits = range(0, nb_albums, 10)
    if not limits[-1] == nb_albums:
        limits.append(nb_albums)
    for start, end in zip(limits[:-1], limits[1:]):
        logging.info('Processing album %i to %i ...', start, end)
        pbar.update(start)
        while True:
            try:
                #TODO: use an API function
                command = {"jsonrpc": "2.0",
                        "method": "AudioLibrary.GetAlbums",
                         "params": {
                            "properties": [
                                "title", 
                                "artist", 
                                "year"],
                            "limits": { 
                                "start": start, 
                                "end": end } },
                        "id": 1}
                ret = kodi_api.call_api(obj.kodi_params, command)
                for album in ret['result']['albums']:
                    obj.albums[album['albumid']] = {}
                    obj.albums[album['albumid']]['title'] = album['title']
                    obj.albums[album['albumid']]['artist'] = album['artist'][0]
                    obj.albums[album['albumid']]['year'] = album['year']
                break
            except KeyError:
                logging.info('error when loading library, retry')
    pbar.finish()
    save_albums(obj.albums)
    print

# parsers

def parse_single_int(line):
    '''Parse line for a single int'''
    logging.debug('call function parse_single_int')
    args = str.split(line)
    ret_val = None
    try:
        ret_val = int(args[0])
    except IndexError:
        pass
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

def get_albums_search(search_string, albums):
    '''Internal album indexes for a string search'''
    search_result_title = []
    search_result_artist = []
    for album_id in albums.keys():
        if search_string in albums[album_id]['title'].lower():
            search_result_title.append(album_id)
        if search_string in albums[album_id]['artist'].lower():
            search_result_artist.append(album_id)
    logging.debug('search result by title: %s', search_result_title)
    logging.debug('search result by artist: %s', search_result_artist)
    return sorted(list(set(search_result_title + search_result_artist)))

def get_songs_search(search_string, songs):
    '''Internal song indexes for a string search'''
    search_result_title = []
    search_result_artist = []
    for song_id in songs.keys():
        if search_string in songs[song_id]['title'].lower():
            search_result_title.append(song_id)
        if search_string in songs[song_id]['artist'].lower():
            search_result_artist.append(song_id)
    logging.debug('search result by title: %s', search_result_title)
    logging.debug('search result by artist: %s', search_result_artist)
    return sorted(list(set(search_result_title + search_result_artist)))

def set_songs_sync(server_params, songs):
    '''Sync playcount and rating'''
    logging.debug('call set_songs_sync')
    print
    print "Updating songs rating and playcount (could be long)"
    print
    nb_songs = len(songs)
    logging.debug('number of songs: %i', nb_songs)
    widgets = [
             'Songs: ', Percentage(),
             ' ', Bar(marker='#',left='[',right=']'),
             ' (', Counter(), ' in ' + str(nb_songs) + ') ',
             ETA()]
    pbar = ProgressBar(widgets=widgets, maxval=nb_songs)
    pbar.start()
    limits = range(0, nb_songs, 20)
    nb_update_rating = 0
    nb_update_playcount = 0
    if not limits[-1] == nb_songs:
        limits.append(nb_songs)
    for start, end in zip(limits[:-1], limits[1:]):
        logging.info('Processing song %i to %i ...', start, end)
        pbar.update(start)
        while True:
            #TODO: use an API function
            try:
                command = {"jsonrpc": "2.0",
                        "method": "AudioLibrary.GetSongs",
                         "params": {
                            "properties": [
                                "rating",
                                "playcount",
                                ],
                            "limits": { 
                                "start": start, 
                                "end": end } },
                        "id": 1}
                ret = kodi_api.call_api(server_params, command)
                for r_song in ret['result']['songs']:
                    if songs[r_song['songid']]['rating'] != r_song['rating']:
                        logging.info(
                                'updating rating for %s!',
                                r_song['songid'])
                        songs[r_song['songid']]['rating'] = r_song['rating']
                        nb_update_rating += 1
                    if songs[r_song['songid']]['playcount'] != r_song['playcount']:
                        logging.info(
                                'updating playcount for %s!',
                                r_song['songid'])
                        songs[r_song['songid']]['playcount'] = r_song['playcount']
                        nb_update_playcount += 1
                break
            except KeyError:
                logging.info('error when loading library, retry')
    pbar.finish()
    save_songs(songs)
    print
    print "%i song(s) rating updated" % nb_update_rating
    print "%i song(s) playcount updated" % nb_update_playcount
    print

def get_profile_delta(songs):
    '''Songs id with echonest rating and playcount not up-to-date'''
    logging.debug('call get_profile_delta')
    songs_id_delta = []
    for song_id in songs.keys():
        if not songs[song_id]['rating'] == songs[song_id]['rating_en']:
            songs_id_delta.append(song_id)
            continue
        if not songs[song_id]['playcount'] == songs[song_id]['playcount_en']:
            songs_id_delta.append(song_id)
            continue
    return songs_id_delta

def echonest_sync(api_key, profile_id, songs):
    '''Sync songs with echonest tasteprofile'''
    logging.debug('call echonest_sync')
    #TODO: cache the profile ID
    #TODO: create routines for echonest API calls + HTTP Kodi calls
    en_info = en_api.echonest_info(api_key, profile_id)
    if en_info['total'] == 0:
        logging.info("no songs in tasteprofile, full sync")
        songs_id_delta = songs.keys()
    else:
        logging.info("limit sync to delta")
        songs_id_delta = get_profile_delta(songs)
    nb_songs_delta = len(songs_id_delta)
    print
    print "Sync songs to the tasteprofile (this can be very very long)"
    print
    logging.info('delta size: %i', nb_songs_delta)
    logging.debug('delta songs %s', songs_id_delta)
    widgets = [
            'Songs: ', Percentage(),
            ' ', Bar(marker='#',left='[',right=']'),
            ' (', Counter(), ' in ' + str(nb_songs_delta) + ') ',
            ETA()]
    pbar = ProgressBar(widgets=widgets, maxval=nb_songs_delta)
    pbar.start()
    # slicing
    limits = range(0, nb_songs_delta, 30)
    if not limits[-1] == nb_songs_delta:
        limits.append(nb_songs_delta)
    for start, end in zip(limits[:-1], limits[1:]):
        logging.info('Processing song index from  %i to %i ...', start, end)
        pbar.update(start)
        command = []
        songs_index_slice = range(start, end)
        for song_index in songs_index_slice:
            song_id = songs_id_delta[song_index]
            rating = songs[song_id]['rating'] * 2
            mb_song_id = 'musicbrainz:song:' + songs[song_id]['musicbrainztrackid']
            #TODO: use API function
            command.append({
                "action": 'update',
                "item": {
                    "item_id": str(song_id),
                    "song_id": mb_song_id,
                    "rating": rating, 
                    "play_count": songs[song_id]['playcount']
                    }
                })

            songs[song_id]['rating_en'] = songs[song_id]['rating']
            songs[song_id]['playcount_en'] = songs[song_id]['playcount']
        url = 'http://developer.echonest.com/api/v4/tasteprofile/update'
        headers = {'content-type': 'multipart/form-data'}
        payload = {
                'api_key': api_key,
                'id': profile_id,
                'data': json.dumps(command)}
        logging.debug('command: %s', command)
        r = requests.post(url, headers=headers, params=payload)
        if r.status_code == 200:
            logging.debug('return: %s', r.text)
        else:
            logging.error('return: %s', r.text)
        time.sleep(0.51)
    pbar.finish()
    save_songs(songs)
    print

def echonest_playlist(api_key, profile_id):
    '''Create a premium static playlist'''
    logging.debug('call echonest_playlist')
    #TODO: split in API function + conversion of namespace
    print
    print "Requesting a playlist to echonest ..."
    url = 'http://developer.echonest.com/api/v4/playlist/static'
    payload = {"api_key": api_key,
              "type": 'catalog',
              "seed_catalog": profile_id,
              "bucket": 'id:' + profile_id
              }
    r = requests.get(url, params=payload)
    logging.debug('URL: %s', r.url)
    logging.debug('return: %s', r.text)
    ret = r.json()
    en_songs = ret['response']['songs']
    playlist = []
    for en_song in en_songs:
        en_id = en_song['foreign_ids'][0]['foreign_id']
        kodi_id = en_id.replace(profile_id + ':song:', "")
        playlist.append(int(kodi_id))
    return playlist

def echonest_pl_seed(api_key, profile_id, song_id):
    '''Create a premium static playlist seeded by a song'''
    logging.debug('call echonest_pl_song')
    #TODO: split in API function + conversion of namespace
    print
    print "Requesting a playlist to echonest ..."
    url = 'http://developer.echonest.com/api/v4/playlist/static'
    en_song_id = profile_id + ':song:' + str(song_id)
    payload = {"api_key": api_key,
              "type": 'catalog',
              "seed_catalog": profile_id,
              "song_id": en_song_id,
              "bucket": 'id:' + profile_id
              }
    r = requests.get(url, params=payload)
    logging.debug('URL: %s', r.url)
    logging.debug('return: %s', r.text)
    ret = r.json()
    en_songs = ret['response']['songs']
    playlist = []
    for en_song in en_songs:
        en_id = en_song['foreign_ids'][0]['foreign_id']
        kodi_id = en_id.replace(profile_id + ':song:', "")
        playlist.append(int(kodi_id))
    return playlist

def get_profile_id(api_key):
    '''Get echonest profile profile ID'''
    #TODO: split in unit API functions
    logging.debug('call get_profile_id')
    url = 'http://developer.echonest.com/api/v4/tasteprofile/profile'
    payload = {
            'api_key': api_key,
            'name': PROFILE_NAME}
    r = requests.get(url, params=payload)
    if r.status_code == 400:
        logging.debug('no taste profile found')
        url = 'http://developer.echonest.com/api/v4/tasteprofile/create'
        headers = {'content-type': 'multipart/form-data'}
        payload = {
                'api_key': api_key,
                'name': PROFILE_NAME,
                'type': 'general'}
        r = requests.post(url, headers=headers, params=payload)
        ret = r.json()
        profile_id = ret['response']['id']
    else:
        logging.debug('taste profile found')
        ret = r.json()
        profile_id = ret['response']['catalog']['id'] 
    logging.debug('return: %s', r.text)
    logging.debug('profile id: %s', profile_id)
    return profile_id
def get_profile_id(api_key):
    '''Get echonest profile profile ID'''
    #TODO: split in unit API functions
    logging.debug('call get_profile_id')
    url = 'http://developer.echonest.com/api/v4/tasteprofile/profile'
    payload = {
            'api_key': api_key,
            'name': PROFILE_NAME}
    r = requests.get(url, params=payload)
    if r.status_code == 400:
        logging.debug('no taste profile found')
        url = 'http://developer.echonest.com/api/v4/tasteprofile/create'
        headers = {'content-type': 'multipart/form-data'}
        payload = {
                'api_key': api_key,
                'name': PROFILE_NAME,
                'type': 'general'}
        r = requests.post(url, headers=headers, params=payload)
        ret = r.json()
        profile_id = ret['response']['id']
    else:
        logging.debug('taste profile found')
        ret = r.json()
        profile_id = ret['response']['catalog']['id'] 
    logging.debug('return: %s', r.text)
    logging.debug('profile id: %s', profile_id)
    return profile_id

def playback(kodi_params):
    '''Start playback'''
    logging.debug('call function playback')
    if kodi_api.player_get_active(kodi_params):
        kodi_api.player_play_pause(kodi_params)
    else:
        kodi_api.player_open(kodi_params)

def playback_stop(kodi_params):
    '''Start playback'''
    logging.debug('call function playback stop')
    if kodi_api.player_get_active(kodi_params):
        kodi_api.player_stop(kodi_params)

def populate_playlist(song_ids, kodi_params):
    '''Create a playlist from an array of song_id'''
    print
    print "Populating the playlist... "
    for song_id in song_ids:
        kodi_api.playlist_add(SONG, song_id, kodi_params)
    print "   ... let's rock the house!"

# process return messages

class KodiRemote(cmd.Cmd):
    
    def __init__(self,kodi_params=0):
        # either the commandline options are parsed
        if kodi_params == 0:
            (self.kodi_params, self.api_key, self.command) = get_pykodi_params()
        else:
            # or the custom server arguments are taken
            self.kodi_params=kodi_params
            self.command=0
        cmd.Cmd.__init__(self)
        
    '''Subclass of the cmd class'''
    
    def preloop(self):
        # initialize library description
        self.nb_songs = 0
        self.songs = {}
        self.nb_albums = 0
        self.albums = {}
        # fill data
        get_audio_library(self)
        
        ''' Check if we skip command line and directly execute the passed command'''
        if self.command!=0:
            logging.info("Executing custom command")
            self.onecmd(self.command)                
            #TODO find out how to detect errors.
            quit()
        else:
            # customize prompt
            sys_name = kodi_api.system_friendly_name(self.kodi_params)
            self.prompt = "(" + sys_name + ") "
            fancy_disp.smart_help()

    # albums functions

    def do_albums_random(self, line):
        '''
        Display a random selection of albums
        Usage: albums_random
        '''
        logging.debug('call function do_albums_random')
        albums_pos = random.sample(xrange(self.nb_albums), DISPLAY_NB_LINES)
        fancy_disp.albums_index(albums_pos, self.albums)

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
                (page_nb - 1) * DISPLAY_NB_LINES + 1,
                page_nb * DISPLAY_NB_LINES + 1)
        fancy_disp.albums_index(albums_pos, self.albums)

    def do_albums_recent(self, line):
        '''
        Display recently added albums
        Usage: albums_recent
        '''
        logging.debug('call function do_albums_recent')
        albums_pos = range(
                self.nb_albums + 1 - DISPLAY_NB_LINES, 
                self.nb_albums + 1)
        fancy_disp.albums_index(albums_pos, self.albums)

    def do_albums_search(self, line):
        '''
        Search into the albums
        Usage: albums_search string
            List all albums containing the string in the title or artist.
        '''
        logging.debug('call function do_albums_search')
        search_string = line.lower()
        #TODO: general refactor to album_ids (pos should not be used)
        albums_pos = get_albums_search(search_string, self.albums)
        fancy_disp.albums_index(albums_pos, self.albums)

    # songs functions
    
    def do_songs_page(self, line):
        '''
        Display a given page of the songs library
        Usage: songss_page [page]
            The page is optional, a random page is displayed without it.
        '''
        logging.debug('call function do_songs_page')
        page_nb = parse_single_int(line)
        if not page_nb:
            logging.info('no page number provided')
            page_nb = random.randrange(int(self.nb_songs / 10) + 1)
        songs_pos = range(
                (page_nb - 1) * DISPLAY_NB_LINES + 1,
                page_nb * DISPLAY_NB_LINES + 1)
        fancy_disp.songs_index(songs_pos, self.songs)

    def do_songs_display(self, line):
        '''
        Display details for a given song
        Usage songs_display id
            Display all information about a given song like the playcount
            or the rating.
        '''
        logging.debug('call function do_song_display')
        song_id = parse_single_int(line)
        fancy_disp.songs_details(song_id, self.songs)
    
    def do_songs_search(self, line):
        '''
        Search into the songs
        Usage: songs_search string
            List all songs containing the string in the title or artist.
        '''
        logging.debug('call function do_songs_search')
        search_string = line.lower()
        songs_pos = get_songs_search(search_string, self.songs)
        fancy_disp.songs_index(songs_pos, self.songs)

    def do_songs_sync(self, line):
        '''
        Sync playcount and rating
        Usage: songs_sync
            Sync playcount and rating from the Kodi server to PyKodi.
        '''
        logging.debug('call function do_songs_sync')
        set_songs_sync(self.kodi_params, self.songs)
    
    # playlist functions

    def do_playlist_show(self, line):
        '''
        Show the current audio playlist
        Usage: playlist_show
        '''
        logging.debug('call function do_playlist_show')
        if kodi_api.player_get_active(self.kodi_params):
            properties = kodi_api.player_get_properties(self.kodi_params)
        else:
            properties = None
        song_ids = kodi_api.playlist_get_items(self.kodi_params)
        fancy_disp.playlist(properties, song_ids, self.songs)

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
            #TODO: disp function
            print
            print "Album %i will be added to the playlist" % album_id
            print
        kodi_api.playlist_add(ALBUM, album_id, self.kodi_params)

    def do_playlist_clear(self, line):
        '''
        Clear the playlist
        Usage: playlist_clear
            Remove all items from the current playlist.
        '''
        logging.debug('call function do_playlist_clear')
        kodi_api.playlist_clear(self.kodi_params)

    def do_playlist_tasteprofile(self, line):
        '''
        Create a playlist from echonest taste profile
        Usage: playlist_tasteprofile
            Generate and play a new playlist based on
            echonest taste profile. The current playlist
            is removed before.
        '''
        logging.debug('call function do_playlist_tasteprofile')
        profile_id = get_profile_id(self.api_key)
        while True:
            song_ids = echonest_playlist(self.api_key, profile_id)
            fancy_disp.songs_index(song_ids, self.songs)
            action = fancy_disp.validate_playlist()
            if action <> 'r':
                break
        if action == 'p':
            playback_stop(self.kodi_params)
            kodi_api.playlist_clear(self.kodi_params)
            populate_playlist(song_ids, self.kodi_params) 
            kodi_api.player_open(self.kodi_params)
        print

    def do_playlist_taste_seed(self, line):
        '''
        Create a playlist from echonest taste profile and seeded by a song
        Usage: playlist_tasteprofile song_id
            Generate and play a new playlist based on
            echonest taste profile. The current playlist
            is removed before.
        '''
        #TODO: function for a single logic and several pl methods
        logging.debug('call function do_playlist_tasteprofile')
        song_id = parse_single_int(line)
        profile_id = get_profile_id(self.api_key)
        while True:
            song_ids = echonest_pl_seed(self.api_key, profile_id, song_id)
            fancy_disp.songs_index(song_ids, self.songs)
            action = fancy_disp.validate_playlist()
            if action <> 'r':
                break
        if action == 'p':
            playback_stop(self.kodi_params)
            kodi_api.playlist_clear(self.kodi_params)
            populate_playlist(song_ids, self.kodi_params) 
            kodi_api.player_open(self.kodi_params)
        print

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
            album_index = random.randrange(self.nb_albums)
            album_id = self.albums.keys()[album_index]
            print "Album %i will be played" % album_id
            print
        kodi_api.playlist_clear(self.kodi_params)
        kodi_api.playlist_add(ALBUM, album_id, self.kodi_params)
        kodi_api.player_open(self.kodi_params)

    def do_play_party(self, line):
        '''
        Start a big party!
        Usage: play_party
        '''
        logging.debug('call function do_play_party')
        kodi_api.player_open_party(self.kodi_params)

    def do_play_pause(self, line):
        '''
        Switch to play or pause
        Usage: play_pause
            Switch to pause if playing, switch to play if in pause.
        '''
        logging.debug('call function do_play_pause')
        playback(self.kodi_params)

    def do_play_stop(self, line):
        '''
        Stop the music
        Usage: play_stop
            Stop the music and go home, I repeat, stop the music and go home.
        '''
        logging.debug('call function do_play_stop')
        playback_stop(self.kodi_params)

    def do_play_what(self, line):
        '''
        Detail status of what is currently played
        Usage: play_what
        '''
        logging.debug('call function do_play_what')
        item = kodi_api.player_get_item(self.kodi_params)
        properties = kodi_api.player_get_properties(self.kodi_params)
        items = kodi_api.playlist_get_items(self.kodi_params)
        fancy_disp.now_playing(item, properties)
        fancy_disp.next_playing(properties, items)

    def do_play_favorite(self, line):
        '''
        Like the current song (in your echonest tasteprofile)
        Usage: play_favorite
        '''
        logging.debug('call function do_play_favorite')
        item = kodi_api.player_get_item(self.kodi_params)
        profile_id = get_profile_id(self.api_key)
        en_api.echonest_favorite(self.api_key, profile_id, item['id'])
    
    def do_play_skip(self, line):
        '''
        Skip the current song
        Usage: play_skip
        '''
        logging.debug('call function do_play_skip')
        song_id = kodi_api.player_get_item(self.kodi_params)
        profile_id = get_profile_id(self.api_key)
        kodi_api.player_goto(self.kodi_params)
        en_api.echonest_skip(self.api_key, profile_id, song_id)
        print
        fancy_disp.skip(song_id, self.songs)
        print

    # volume control
    def do_volume(self,percent):
       '''
       Set volume in percent
       Usage: volume 100
       '''
       logging.debug('call function do_volume')
       #TODO percent might not be a number between 0 and 100
       try:            
           kodi_api.player_volume(self.kodi_params,int(percent))
       except:
           logging.error('Volume must be between 0 and 100.')

    # echonest functions

    def do_echonest_sync(self, line):
        '''
        Sync play count and rating with echonest taste profile
        Usage: echonest_sync
        '''
        logging.debug('call function do_echonest_sync')
        profile_id = get_profile_id(self.api_key)
        echonest_sync(self.api_key, profile_id, self.songs)
        
    def do_echonest_info(self, line):
        '''
        Display info about the echonest taste profile.
        Usage: echonest_info
        '''
        logging.debug('call function do_echonest_info')
        profile_id = get_profile_id(self.api_key)
        en_info = en_api.echonest_info(self.api_key, profile_id)
        #TODO: create disp function
        print
        print en_info
        print

    def do_echonest_read(self, line):
        '''
        Display data for a given item.
        Usage: echonest_read item_id
        '''
        logging.debug('call function do_echonest_info')
        profile_id = get_profile_id(self.api_key)
        item_id = parse_single_int(line)
        en_read = en_api.echonest_read(self.api_key, profile_id, item_id)
        print
        print en_read
        print

    def do_echonest_delete(self, line):
        '''
        Delete echonest taste profile.
        Usage: echonest_delete
        '''
        logging.debug('call function do_echonest_delete')
        profile_id = get_profile_id(self.api_key)
        if fancy_disp.sure_delete_tasteprofile(self.api_key, profile_id):
        #TODO: insert a validation prompt
            en_api.echonest_delete(self.api_key, profile_id)

    def do_EOF(self, line):
        '''Override end of file'''
        logging.info('Bye!')
        print 'Bye!'
        return True

def main():
    '''Where everything starts'''

    remote_controller = KodiRemote()
    remote_controller.cmdloop()

if __name__ == '__main__':
    main()
