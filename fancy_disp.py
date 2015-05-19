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

#TODO: song_ids and not songs_id + just albums or songs
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

def songs_index(songs_id, kodi_songs):
    '''Display songs list from internal index'''
    logging.debug('call disp_songs_index')
    print
    for i, song_id in enumerate(songs_id):
        print ("%02i. \"%s\" by %s (%s) [%i]") % (
                i + 1,
                kodi_songs[song_id]['title'],
                kodi_songs[song_id]['artist'],
                kodi_songs[song_id]['year'],
                song_id )

def songs_details(song_id, kodi_songs):
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

def playlist(properties, song_ids, songs):
    '''Display playlist'''
    if properties:
        position = properties['position']
    else:
        position = -1
    print
    if song_ids:
        for i, song_id in enumerate(song_ids):
            if i == position:
                print ">> ",
            else:
                print "   ",
            print "%02i. \"%s\" by %s (%s) [%s]" % (
                    i + 1,
                    songs[song_id]['artist'],
                    songs[song_id]['title'],
                    songs[song_id]['year'],
                    song_id )
    else:
        print "[playlist empty]"
    print

def now_playing(item, properties):
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

def next_playing(properties, items):
    '''Display the next playing part of display_what'''
    print
    if properties:
        print "(%i / %i) - Next: %s - %s" % (
                properties['position'] + 1,
                len(items),
                items[properties['position'] + 1]['artist'][0],
                items[properties['position'] + 1]['title'] )
        print

def skip(song_id, songs):
    '''Confirm skip'''
    print "You just have skipped the song \"%s\" by %s [%i]." % (
            songs[song_id]['title'], songs[song_id]['artist'], song_id)

def favorite(song_id, songs):
    '''Confirm favorite'''
    print "The song \"%s\" by %s [%i] is now a favorite." % (
            songs[song_id]['title'], songs[song_id]['artist'], song_id)

def play_album(album_id, albums):
    '''Confirm play album'''
    print "Let's play the album \"%s\" by %s [%i]." % (
            albums[album_id]['title'], albums[album_id]['artist'], album_id)

def echonest_read(song_data):
    '''Display echonest song data'''
    # clean display
    if 'rating' in song_data:
        rating = song_data['rating']
    else:
        rating = 0
    if 'play_count' in song_data:
        play_count = song_data['play_count']
    else:
        play_count = 0
    if 'skip_count' in song_data:
        skip_count = song_data['skip_count']
    else:
        skip_count = 0
    favorite = 'favorite' in song_data
    banned = 'banned' in song_data
    # output
    print "\"%s\" by %s" % (song_data['song_name'], song_data['artist_name'])
    print
    print "   Echonest ID: \t%s" % song_data['song_id']
    print "   Foreign ID: \t\t%s" % song_data['foreign_id']
    print "   MusicBrainz ID: \t%s" % song_data['request']['song_id']
    print
    print "   Date added: %s - Last modified: %s" % (
            song_data['date_added'], song_data['last_modified'])
    print
    print "   This song has been played %i time(s) and skipped %i time(s)" % (
            play_count, skip_count)
    print "   Rating: %s - Favorite: %s - Banned: %s" % (
            rating, favorite, banned)
    print
    print "   Song type(s): %s" % (", ".join(song_data['song_type']))
    print
    print "   Song currency: \t%s" % (song_data['song_currency'])
    print "   Song hotttnesss: \t%s" % (song_data['song_hotttnesss'])
    print
    print "   Artist familiarity: \t%s" % (song_data['artist_familiarity'])
    print "   Artist hotttnesss: \t%s" % (song_data['artist_hotttnesss'])
    print "   Artist discovery: \t%s" % (song_data['artist_discovery'])

# prompt for confirmation

def validate_playlist():
    '''Request what should be done with a playlist proposal.'''
    print
    rep = raw_input(
            "What now? (P)lay or (R)egenerate? Anything else to cancel: ")
    return rep.lower()

def sure_delete_tasteprofile(api_key, profile_id):
    '''Warning before taste profile deletion.'''
    print
    print "WARNING: you are about to delete your taste profile. All your"
    print "favorite, ban and skip data will be lost. playcount and rating"
    print "data are safe in your Kodi library."
    print
    rep = raw_input("Are you sure (Y/c)? ")
    return rep == 'Y'

# stub for smart help

def smart_help():
    '''Help messages that make sense.'''
    # welcome message
    print
    print "For a quick start, try play_album"
    print
