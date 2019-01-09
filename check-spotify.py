from datetime import datetime
import json
import random
import smtplib
import sys
from time import sleep
import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials
from config import Config
from app.email_report import send_report, send_recommendation_report

# Spotify API authentication setup
# scope: Spotify API authorization scopes required to modify and private playlists. Some of my playlists are public, so that scope is required as well
scope = 'playlist-modify-private playlist-read-private playlist-modify-public'
token = util.prompt_for_user_token(Config.SPOTIFY_USER, scope, client_id=Config.CLIENT_ID, client_secret=Config.CLIENT_SECRET, redirect_uri=Config.REDIRECT_URI)
sp = get_spotify_client()

# I'm not sure if delcaring lists here is necessary or not. I'll see what I can do about these later
artist_uris = []
artist_names = []
all_albums = []
ALBUM_TYPES = ['single','album']

# Used to compare against release dates for albums. We only want results newer than January 1st, 2018. This will require updating every year, because I don't want to add past releases to any artist playlist
now = datetime.strptime('2018-01-01', '%Y-%m-%d')

def get_spotify_client():
    clientmgr = SpotifyClientCredentials(Config.CLIENT_ID, Config.CLIENT_SECRET)
    token = util.prompt_for_user_token(Config.SPOTIFY_USER, scope, client_id=Config.CLIENT_ID, client_secret=Config.CLIENT_SECRET, redirect_uri=Config.REDIRECT_URI)
    return spotipy.Spotify(auth=token, client_credentials_manager=clientmgr)

def get_previous_additions():
    """
    Returns a list of all music previously added to playlists via this script.
    """
    with open('album_history.txt', 'r') as history_file:
        previous_additions = history_file.read().splitlines()

    return previous_additions

def get_random_recommendations(client, uris):
    """
    Return a list of recommended artists from a seed of 5 artists randomly chosen from the library.
    """
    random_artists = random.sample(uris, 5)
    recs = []
    sp = client
    
    try:
        recommendations = sp.recommendations(seed_artists=random_artists, limit=100)
    except spotipy.client.SpotifyException:
        sp = get_spotify_client()
        recommendations = sp.recommendations(seed_artists=random_artists, limit=100)

    for rec in recommendations['tracks']:
        band = rec['artists'][0]['name']
        band_uri = rec['artists'][0]['uri']
        band_genre = ', '.join(sp.artist(band_uri)['genres'])
        if len(band_genre) > 0:
            if band not in recs and band not in artist_names:
                recs.append(band + f' ({band_genre})')
        else:
            if band not in recs and band not in artist_names:
                recs.append(band)

    return recs

# Retrieve the first 50 playlists from the Spotify account (maximum that can be retrieved per API call)
try:
    results_playlists = sp.user_playlists(Config.SPOTIFY_USER, limit=50, offset=0)
except spotipy.client.SpotifyException:
    sp = get_spotify_client()
    results_playlists = sp.user_playlists(Config.SPOTIFY_USER, limit=50, offset=0)

# As we can only retrieve 50 playlists per API call, we'll need a while loop to page through the results until we've process all playlists (a bit over 100 in my case)
while results_playlists:
    for playlist in results_playlists['items']:

        # Playlists prefixed with . are skipped (mostly for artists that I don't care if they release new music)
        if playlist['name'].startswith('.'):
            continue

        # Skip any playlists we don't own
        if playlist['owner']['id'] != Config.SPOTIFY_USER:
            continue

        albums_playlist = []
        name = playlist['name']
        pid = playlist['id']

        #print(f'{name} - {pid}') # For tracking down which playlist the script errors at

        # Retrieve the tracks from the playlist
        try:
            results = sp.user_playlist(Config.SPOTIFY_USER, pid, fields="tracks,next")
        except spotipy.client.SpotifyException:
            sp = get_spotify_client()
            results = sp.user_playlist(Config.SPOTIFY_USER, pid, fields="tracks,next")

        tracks = results['tracks']
        artist = tracks['items'][0]['track']['artists'][0]['name']

        # artist_names is used in get_random_recommendations() so we don't get recommendations for bands that already have playlists in our library
        if artist not in artist_names:
            artist_names.append(artist)

        artist_uri = tracks['items'][0]['track']['artists'][0]['uri'].split(':')[2]

        # We create a list of artist URIs so we can use them as seeds for artist recommendations
        if artist_uri not in artist_uris:
            artist_uris.append(artist_uri)

        # playlist_tracks helps us keep track of which singles are already in an artist's library. the album names for new singles are named after the song, so if we compare all tracks to all albums - we won't get duplicate singles added
        playlist_tracks = []

        # Take the album URI from every track in the playlist and add it to a list, we'll use this to help detect new music that's not in the playlist already
        for track in tracks['items']:
            album_uri = track['track']['album']['uri']
            playlist_tracks.append(track['track']['name'])
            if album_uri not in albums_playlist:
                albums_playlist.append(album_uri)
            else:
                continue

        # If there's more than 100 tracks in a playlist, this will page through all results and process those as well
        if tracks['next']:
            tracks = sp.next(tracks)
            for track in tracks['items']:
                album_uri = track['track']['album']['uri']
                trackname = track['track']['name']

                if trackname not in playlist_tracks:
                    playlist_tracks.append(track['track']['name'])

                if album_uri not in albums_playlist:
                    albums_playlist.append(album_uri)
                else:
                    continue

        new_albums = []
        new_tracks = []

        # Create a list of URIs for all of the artist's releases (albums and singles)
        for t in ALBUM_TYPES:
            try:
                res = sp.artist_albums(artist_uri, album_type=t)
            except spotipy.client.SpotifyException:
                sp = get_spotify_client()
                res = sp.artist_albums(artist_uri, album_type=t)

            albums = res['items']

            # # If there's more releases than one API call can return, this will page through all results and add those to the list as well
            while res['next']:
                try:
                    res = sp.next(res)
                except spotipy.client.SpotifyException:
                    sp = get_spotify_client()
                    res = sp.next(res)

                albums.extend(res['items'])
            sleep(1)

            for album in albums:
                if album['uri'] not in albums_playlist:
                    if "deluxe" not in album['name'].lower():
                        release_date = album['release_date']
                    else:
                        # We don't want Deluxe versions of albums added, so we skip these
                        continue

                    # We need the date of the release as a datetime, but some releases only have a year listed, some have a year and a month, and some have the full year/month/date
                    if len(release_date) == 4:
                        release_date = datetime.strptime(release_date, '%Y')
                    elif len(release_date) == 7:
                        release_date = datetime.strptime(release_date, '%Y-%m')
                    else:
                        release_date = datetime.strptime(release_date, '%Y-%m-%d')

                    # If the release was not from this year, skip it
                    if release_date < now:
                        continue

                    if album['name'] in playlist_tracks:
                        continue

                    albuminfo = f"{t}: {album['artists'][0]['name']} - {album['name']}"
                    print(albuminfo)
                    all_albums.append(albuminfo)
                    uri = album['uri'].split(':')[2]
                    new_albums.append(uri)

        for album in new_albums:
            try:
                result = sp.album_tracks(album, limit=50, offset=0)
            except spotipy.client.SpotifyException:
                sp = get_spotify_client()
                result = sp.album_tracks(album, limit=50, offset=0)

            tracks = result['items']

            for track in tracks:
                uri = track['uri'].split(':')[2]
                new_tracks.append(uri)
            sleep(1)

        # Add the new tracks to the playlist
        if new_tracks:
            sp.user_playlist_add_tracks(Config.SPOTIFY_USER, pid, tracks=new_tracks)

        sleep(1)

    if results_playlists['next']:
        try:
            results_playlists = sp.next(results_playlists)
        except spotipy.client.SpotifyException:
            sp = get_spotify_client()
            results_playlists = sp.next(results_playlists)
    else:
        results_playlists = None

# If new music has been found for an artist in my collection, send an email with the new additions. Otherwise, send a report of random recommendations based on artists in the library.
if len(all_albums) > 0:
    previous_albums = get_previous_additions()
    send_report(all_albums, previous_albums)

    # Append new additions to album history log
    with open('album_history.txt', 'a') as history_file:
        for album in all_albums:
            msg = f'{album}\n'
            history_file.write(msg)

else:
    previous_albums = get_previous_additions()
    random_recommendations = get_random_recommendations(sp, artist_uris)
    send_recommendation_report(random_recommendations, previous_albums)
    print('No new music found. Sending random recommendations instead.')
