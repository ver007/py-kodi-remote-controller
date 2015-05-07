#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2015 Arn-O. See the LICENSE file at the top-level directory of this
# distribution and at
# https://github.com/Arn-O/py-kodi-remote-controller/blob/master/LICENSE.

'''
Kodi remote controller based on HTTP/TCP transport, JSON and using the (cmd) interface.
'''

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

# global constants
BUFFER_SIZE = 1024
DISPLAY_NB_LINES = 10
PROFILE_NAME = 'Kodi library'

#TODO: add instrospect
#TODO: display number of transactions calls in echonest API
#TODO: persistent sync data
#TODO: delta for echonest sync

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
    args = parser.parse_args()
    server_params = {}
    server_params['tcp'] = args.tcp
    server_params['ip'] = args.ip
    server_params['port'] = args.port
    server_params['user'] = args.user
    server_params['password'] = args.password
    return server_params, args.echonest_key, args.verbosity

# API call management

def call_api(server_params, command):
    if server_params['tcp']:
        ret = call_api_tcp(
                server_params['ip'], 
                server_params['port'],
                command)
    else:
        ret = call_api_http(server_params, command)
    return ret

def call_api_http(server_params, command):
    logging.debug('call call_api_http')
    logging.debug('command: %s', command)
    kodi_url = 'http://' + server_params['ip'] +  ':' + str(server_params['port']) + '/jsonrpc'
    headers = {'Content-Type': 'application/json'}
    r = requests.post(
            kodi_url,
            data=json.dumps(command),
            headers=headers,
            auth=(server_params['user'], server_params['password']))
    ret = r.json()
    logging.debug('url: %s', r.url)
    logging.debug('status code: %s', r.status_code)
    logging.debug('text: %s', r.text)
    return ret

def call_api_tcp(ip, port, command):
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
    nb_songs = get_nb_songs(obj.kodi_params)
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
                ret = call_api(obj.kodi_params, command)
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
                break
            except KeyError:
                #TODO: improve error catching, limit to API errors
                logging.info('error when loading library, retry')
    pbar.finish()
    # Loading albums
    nb_albums = get_nb_albums(obj.kodi_params)
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
                ret = call_api(obj.kodi_params, command)
                for album in ret['result']['albums']:
                    obj.albums[album['albumid']] = {}
                    obj.albums[album['albumid']]['title'] = album['title']
                    obj.albums[album['albumid']]['artist'] = album['artist'][0]
                    obj.albums[album['albumid']]['year'] = album['year']
                break
            except KeyError:
                logging.info('error when loading library, retry')
    pbar.finish()
    print
    f = open('songs.pickle', 'wb')
    pickle.dump(obj.songs, f)
    f.close()
    f = open('albums.pickle', 'wb')
    pickle.dump(obj.albums, f)
    f.close()

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
    nb_songs = len(songs)
    logging.debug('number of songs: %i', nb_songs)
    limits = range(0, nb_songs, 20)
    if not limits[-1] == nb_songs:
        limits.append(nb_songs)
    for start, end in zip(limits[:-1], limits[1:]):
        logging.info('Processing song %i to %i ...', start, end)
        while True:
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
                ret = call_api(server_params, command)
                for r_song in ret['result']['songs']:
                    if songs[r_song['songid']]['rating'] != r_song['rating']:
                        logging.info(
                                'updating rating for %s!',
                                r_song['songid'])
                        songs[r_song['songid']]['rating'] = r_song['rating']
                    if songs[r_song['songid']]['playcount'] != r_song['playcount']:
                        logging.info(
                                'updating playcount for %s!',
                                r_song['songid'])
                        songs[r_song['songid']]['playcount'] = r_song['playcount']
                break
            except KeyError:
                logging.info('error when loading library, retry')

def echonest_sync(api_key, profile_id, songs):
    '''Sync songs with echonest tasteprofile'''
    logging.debug('call echonest_sync')
    #TODO: cache the profile ID
    #TODO: create routines for echonest API calls + HTTP Kodi calls
    nb_songs = len(songs)
    # slicing
    limits = range(1, (nb_songs + 1), 30)
    if not limits[-1] == (nb_songs + 1):
        limits.append(nb_songs + 1)
    for start, end in zip(limits[:-1], limits[1:]):
        logging.info('Processing song %i to %i ...', start, end)
        command = []
        songs_id_slice = range(start, end)
        for song_id in songs_id_slice:
            rating = songs[song_id]['rating'] * 2
            mb_song_id = 'musicbrainz:song:' + songs[song_id]['musicbrainztrackid']
            command.append({
                "action": 'update',
                "item": {
                    "item_id": str(song_id),
                    "song_id": mb_song_id,
                    "rating": rating, 
                    "play_count": songs[song_id]['playcount']
                    }
                })
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
            logging.info('return: %s', r.text)
        time.sleep(0.51)

def echonest_playlist(api_key, profile_id):
    '''Create a premium static playlist'''
    logging.debug('call echonest_playlist')
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
        playlist.append(kodi_id)
    return playlist

def echonest_info(api_key, profile_id):
    '''Display info about echonest profile'''
    logging.debug('call echonest_info')
    url = 'http://developer.echonest.com/api/v4/tasteprofile/profile'
    payload = {"api_key": api_key,
              "id": profile_id
              }
    r = requests.get(url, params=payload)
    print(r.url)
    print(r.text)
    url = 'http://developer.echonest.com/api/v4/tasteprofile/read'
    payload = {"api_key": api_key,
              "id": profile_id
              }
    r = requests.get(url, params=payload)
    print(r.url)
    print(r.text)

def echonest_delete(api_key, profile_id):
    '''Delete echonest tasteprofile'''
    logging.debug('call echonest_delete')
    url = 'http://developer.echonest.com/api/v4/tasteprofile/delete'
    headers = {'content-type': 'multipart/form-data'}
    payload = {"api_key": api_key,
              "id": profile_id
              }
    r = requests.post(url, headers=headers, params=payload)
    print(r.url)
    print(r.text)

# getters

def playlist_get_items(server_params):
    '''Get all items from the audio playlist'''
    logging.debug('call playlist_get_items')
    command = {"jsonrpc": "2.0",
            "method": "Playlist.GetItems",
            "params": {
                "playlistid": 0,
                "properties": [
                    "title", 
                    "artist", 
                    "duration", 
                    "track"] },
            "id": 1}
    ret = call_api(server_params, command)
    display_result(ret)
    tracks = None
    try:
        tracks = ret['result']['items']
    except KeyError:
        pass
    return tracks

def get_item(server_params):
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
    ret = call_api(server_params, command)
    display_result(ret)
    item = None
    try:
        item = ret['result']['item']
    except KeyError:
        pass
    return item

def get_properties(server_params):
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
    ret = call_api(server_params, command)
    display_result(ret)
    result = None
    try:
        result = ret['result']
    except KeyError:
        logging.debug('no properties found, player not active')
        pass
    return result

def system_friendly_name(server_params):
    '''Get the system name and hostname'''
    command = {"jsonrpc": "2.0",
            "method": "XBMC.GetInfoLabels",
            "params": {
                "labels": ["System.FriendlyName"] },
            "id": 1}
    ret = call_api(server_params, command)
    display_result(ret)
    return ret['result']['System.FriendlyName']

def get_nb_songs(server_params):
    '''Give the total number of songs in the library'''
    command = {"jsonrpc": "2.0",
            "method": "AudioLibrary.GetSongs",
            "params": {
                "limits": {
                    "start": 0, 
                    "end": 1 } },
            "id": 1}
    ret = call_api(server_params, command)
    display_result(ret)
    return ret['result']['limits']['total']

def get_nb_albums(server_params):
    '''Give the total number of albums in the library'''
    command = {"jsonrpc": "2.0",
            "method": "AudioLibrary.GetAlbums",
            "params": {
                "limits": {
                    "start": 0, 
                    "end": 1 } },
            "id": 1}
    ret = call_api(server_params, command)
    display_result(ret)
    return ret['result']['limits']['total']

# setters

def playlist_clear(server_params):
    '''Clear the audio playlist'''
    logging.debug('call function playlist_clear')
    command = {"jsonrpc": "2.0",
            "method": "Playlist.Clear",
            "params": {
                "playlistid": 0 },
            "id": 1}
    ret = call_api(server_params, command)
    display_result(ret)

def playlist_add(album_id, server_params):
    '''Add an album to the audio playlist'''
    logging.debug('call function playlist_add')
    command = {"jsonrpc": "2.0",
            "method": "Playlist.Add",
            "params": {
                "playlistid": 0,
                "item": {
                    "albumid": album_id } },
            "id": 1}
    ret = call_api(server_params, command)
    display_result(ret)

def playlist_add_songs(song_ids, server_params):
    '''Add a list of songs to the audio playlist'''
    logging.debug('call function playlist_add')
    for song_id in song_ids:
        command = {"jsonrpc": "2.0",
                "method": "Playlist.Add",
                "params": {
                    "playlistid": 0,
                    "item": {
                        "songid": int(song_id) } },
                "id": 1}
        ret = call_api(server_params, command)
        display_result(ret)

def player_get_active(server_params):
    '''Returns active audio players (boolean)'''
    logging.debug('call function playlist_get_active')
    command = {"jsonrpc": "2.0",
            "method": "Player.GetActivePlayers",
            "id": 1,
            }
    ret = call_api(server_params, command)
    display_result(ret)
    if ret['result']:
        active = True
    else:
        active = False
    return active

def player_open(server_params):
    '''Open the audio playlist'''
    logging.debug('call function player_open')
    command = {"jsonrpc": "2.0",
            "method": "Player.Open",
            "params": {
                "item": {
                    "playlistid": 0 } },
            "id": 1}
    ret = call_api(server_params, command)
    display_result(ret)

def player_open_party(server_params):
    '''Open the audio player in partymode'''
    logging.debug('call function player_open_party')
    command = {"jsonrpc": "2.0",
            "method": "Player.Open",
            "params": {
                "item": {
                    "partymode": "music" } },
            "id": 1}
    ret = call_api(server_params, command)
    display_result(ret)

def player_play_pause(server_params):
    '''Pauses or unpause playback and returns the new state'''
    logging.debug('call function player_play_pause')
    command = {"jsonrpc": "2.0",
            "method": "Player.PlayPause",
            "params": {
                "playerid": 0,
                },
            "id": 1}
    ret = call_api(server_params, command)
    display_result(ret)

def player_stop(server_params):
    '''Stops playback'''
    logging.debug('call function player_stop')
    command = {"jsonrpc": "2.0",
            "method": "Player.Stop",
            "params": {
                "playerid": 0 },
            "id": 1}
    ret = call_api(server_params, command)
    display_result(ret)

# display function

def disp_albums_index(albums_id, kodi_albums):
    '''Display albums list from internal index'''
    logging.debug('call disp_albums_index')
    print
    for i, album_id in enumerate(albums_id):
        print ("%02i. %s by %s (%s) [%i]") % (
                i + 1,
                kodi_albums[album_id]['title'],
                kodi_albums[album_id]['artist'],
                kodi_albums[album_id]['year'],
                album_id )
    print
    print "Total number of albums: %i" % len(kodi_albums)
    print

def disp_songs_index(songs_id, kodi_songs):
    '''Display songs list from internal index'''
    logging.debug('call disp_songs_index')
    print
    for i, song_id in enumerate(songs_id):
        print ("%02i. %s by %s (%s) [%i]") % (
                i + 1,
                kodi_songs[song_id]['title'],
                kodi_songs[song_id]['artist'],
                kodi_songs[song_id]['year'],
                song_id )
    print
    print "Total number of songs: %i" % len(kodi_songs)
    print

def disp_songs_details(song_id, kodi_songs):
    '''Display song details from song id'''
    logging.debug('call disp_songs_details')
    print
    print ("%s by %s (%s)") % (
            kodi_songs[song_id]['title'],
            kodi_songs[song_id]['artist'],
            kodi_songs[song_id]['year'])
    print ("   Playcount: %i") % kodi_songs[song_id]['playcount']
    print ("   Rating: %i") % kodi_songs[song_id]['rating']
    print ("   MusicBrainz ID: %s") % kodi_songs[song_id]['musicbrainztrackid']
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
    #TODO: merge somehow with songs_display 
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

def get_profile_id(api_key):
    '''Get echonest profile profile ID'''
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

# process return messages

class KodiRemote(cmd.Cmd):
        
    '''Subclass of the cmd class'''
    
    def preloop(self):
        '''Override and used for class variable'''
        (self.kodi_params, self.api_key, verbosity) = get_pykodi_params()
        if verbosity == 2:
            logging.basicConfig(level=logging.DEBUG)
        elif verbosity == 1:
            logging.basicConfig(level=logging.INFO)
        logging.info('Kodi controller started in verbosity mode ...')
        logging.debug('... and even in high verbosity mode!')
        # initialize library description
        self.nb_songs = 0
        self.songs = {}
        self.nb_albums = 0
        self.albums = {}
        # fill data
        get_audio_library(self)
        # customize prompt
        sys_name = system_friendly_name(self.kodi_params)
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
        disp_albums_index(albums_pos, self.albums)

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
        disp_albums_index(albums_pos, self.albums)

    def do_albums_recent(self, line):
        '''
        Display recently added albums
        Usage: albums_recent
        '''
        logging.debug('call function do_albums_recent')
        albums_pos = range(
                self.nb_albums + 1 - DISPLAY_NB_LINES, 
                self.nb_albums + 1)
        disp_albums_index(albums_pos, self.albums)

    def do_albums_search(self, line):
        '''
        Search into the albums
        Usage: albums_search string
            List all albums containing the string in the title or artist.
        '''
        logging.debug('call function do_albums_search')
        search_string = line.lower()
        albums_pos = get_albums_search(search_string, self.albums)
        disp_albums_index(albums_pos, self.albums)

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
        disp_songs_index(songs_pos, self.songs)

    def do_songs_display(self, line):
        '''
        Display details for a given song
        Usage songs_display id
            Display all information about a given song like the playcount
            or the rating.
        '''
        logging.debug('call function do_song_display')
        song_id = parse_single_int(line)
        disp_songs_details(song_id, self.songs)
    
    def do_songs_search(self, line):
        '''
        Search into the songs
        Usage: songs_search string
            List all songs containing the string in the title or artist.
        '''
        logging.debug('call function do_songs_search')
        search_string = line.lower()
        songs_pos = get_songs_search(search_string, self.songs)
        disp_songs_index(songs_pos, self.songs)

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
        properties = get_properties(self.kodi_params)
        tracks = playlist_get_items(self.kodi_params)
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
        playlist_add(album_id, self.kodi_params)

    def do_playlist_clear(self, line):
        '''
        Clear the playlist
        Usage: playlist_clear
            Remove all items from the current playlist.
        '''
        logging.debug('call function do_playlist_clear')
        playlist_clear(self.kodi_params)

    def do_playlist_tasteprofile(self, line):
        '''
        Create a playlist from echonest test profile
        Usage: playlist_tasteprofile
            Generate and play a new playlist based on
            echonest taste profile. The current playlist
            is removed before.
        '''
        logging.debug('call function do_playlist_add')
        profile_id = get_profile_id(self.api_key)
        songids = echonest_playlist(self.api_key, profile_id)
        playlist_clear(self.kodi_params)
        playlist_add_songs(songids, self.kodi_params)

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
        playlist_clear(self.kodi_params)
        playlist_add(album_id, self.kodi_params)
        player_open(self.kodi_params)

    def do_play_party(self, line):
        '''
        Start a big party!
        Usage: play_party
        '''
        logging.debug('call function do_play_party')
        player_open_party(self.kodi_params)

    def do_play_pause(self, line):
        '''
        Switch to play or pause
        Usage: play_pause
            Switch to pause if playing, switch to play if in pause.
        '''
        logging.debug('call function do_play_pause')
        if player_get_active(self.kodi_params):
            player_play_pause(self.kodi_params)
        else:
            player_open(self.kodi_params)

    def do_play_stop(self, line):
        '''
        Stop the music
        Usage: play_stop
            Stop the music and go home, I repeat, stop the music and go home.
        '''
        logging.debug('call function do_play_stop')
        player_stop(self.kodi_params)

    def do_play_what(self, line):
        '''
        Detail status of what is currently played
        Usage: play_what
        '''
        logging.debug('call function do_play_what')
        item = get_item(self.kodi_params)
        properties = get_properties(self.kodi_params)
        items = playlist_get_items(self.kodi_params)
        disp_now_playing(item, properties)
        disp_next_playing(properties, items)

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
        echonest_info(self.api_key, profile_id)

    def do_echonest_delete(self, line):
        '''
        Delete echonest taste profile.
        Usage: echonest_info
        '''
        logging.debug('call function do_echonest_delete')
        profile_id = get_profile_id(self.api_key)
        echonest_delete(self.api_key, profile_id)

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
