#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2015 Arn-O. See the LICENSE file at the top-level directory of this
# distribution and at
# https://github.com/Arn-O/py-kodi-remote-controller/blob/master/LICENSE.

'''
Module of display function for PyKodi.
'''

import logging

def albums_index(albums_id, kodi_albums):
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
    print "   Playcount: %i (%i)" % (
            kodi_songs[song_id]['playcount'],
            kodi_songs[song_id]['playcount_en'])
    print "   Rating: %i (%i)" % (
            kodi_songs[song_id]['rating'],
            kodi_songs[song_id]['rating_en'])
    print "   MusicBrainz ID: %s" % kodi_songs[song_id]['musicbrainztrackid']
    print

def playlist(properties, tracks):
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
