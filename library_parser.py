#!/usr/bin/env python

import json
import sys
import requests
import urllib.parse
from loguru import logger

# I need to download every track that's in here, and every album and artist marked as "inLibrary"
# (For those i just need to download the traks)
# {
#     'artist1': {
#         'spotify_uri': "spotify:artist:uri",
#         'albums': {
#             'album1': {
#                 'spotify_uri': "spotify:album:uri",
#                 'tracks': {
#                     'track1': {
#                         'spotify_uri': "spotify:track:uri"
#                     },
#                 }
#             },
#         },
#     },
# }
data = {}

loglevel = "DEBUG"
completeAlbum = True
completeArtist = False

downloadURI = []


class Spotify:
    def __init__(self):

        logger.debug("Loading config.json")
        with open("config.json", 'r') as file:
            content = json.load(file)

            self.client_id = content['client_id']
            self.client_secret = content['client_secret']

        auth = requests.post(
            'https://accounts.spotify.com/api/token',
            {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
        )

        if auth.status_code != 200:
            logger.critical("error while authenticating with spotify servers.")
            exit(1)

        self.base_url = "https://api.spotify.com/v1"
        self.access_token = auth.json()['access_token']
        self.headers = {
            'Authorization': f'Bearer {self.access_token}'
        }

        logger.debug(f"access token: {self.access_token}")

    def getURI(self, artist, album=None, track=None):
        req_type = "track" if track is not None else "album" if album is not None else "artist"
        query = ""

        if track is not None:
            query += f"track:{track} "
        elif album is not None:
            query += f"album:{album} "
        query += f"artist:{artist}"

        url = self.base_url + \
            f"/search?type={req_type}&q={urllib.parse.quote(query)}"

        res = requests.get(url, headers=self.headers).json()

        try:
            uri = res[req_type + 's']['items'][0]['uri']
            logger.debug(f"Found {uri} for '{artist}' - '{album}' - {track}")
        except IndexError:
            # IndexError for "L'Officina Della Camomilla". 
            # The problem is not caused from " ' ", I tested it.
            # The problem is presente even for some album.
            logger.error(f"Cannot get uri for '{artist}' - '{album}' - '{track}'. Do it manually.")
            uri = ""

        return uri

def addArtist(artistName: str, spotify_uri=None, albums=None, inLibrary=False):
    if artistName in data:
        return False

    data[artistName] = {
        'spotify_uri': spotify_uri,
        'inLibrary': inLibrary,
        'albums': {} if albums is None else albums,
    }

    logger.debug(
        f"addArtist: Added '{artistName}': {json.dumps(data[artistName])}")

    return True


def addAlbum(albumName, artistName, spotify_uri=None, tracks=None, inLibrary=False):
    if not addArtist(artistName) and albumName in data[artistName]['albums']:
        return False

    data[artistName]['albums'][albumName] = {
        'spotify_uri': spotify_uri,
        'inLibrary': inLibrary,
        'tracks': {} if tracks is None else tracks,
    }

    logger.debug(
        f"addAlbum: In '{artistName}',\t added '{albumName}': {json.dumps(data[artistName]['albums'][albumName])}")

    return True


def addTrack(trackName, albumName, artistName, spotify_uri=None, inLibrary=False):
    if not addAlbum(albumName, artistName) and trackName in data[artistName]['albums'][albumName]['tracks']:
        return False

    data[artistName]['albums'][albumName]['tracks'][trackName] = {
        'spotify_uri': spotify_uri,
        'inLibrary': inLibrary}

    logger.debug(
        f"addTrack: In '{artistName}'\t'{albumName}',\t added '{trackName}': {json.dumps(data[artistName]['albums'][albumName]['tracks'][trackName])}")

    return True


def getArtist(artistName):
    return data[artistName]


def getAlbum(artistName, albumName):
    return data[artistName]['albums'][albumName]


def getTrack(artistName, albumName, trackName):
    return data[artistName]['albums'][albumName]['tracks'][trackName]


# Returns a list in the form:
# [
#     {
#         'name': "playlist name",
#         'items': [
#             {
#                 'trackName': "track name",
#                 'albumName': "album name",
#                 'artistName': "artist name"
#             }
#         ]
#     }
# ]


def getPlaylists(data: list):
    result = []
    for playlist in data:
        items = []

        for item in playlist['items']:
            items.append({
                'trackName': item['track']['trackName'],
                'albumName': item['track']['albumName'],
                'artistName': item['track']['artistName'],
                'spotify_uri': item['track']['trackUri']
            })

        result.append({
            'name': playlist['name'],
            'items': items
        })

    return result


logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YY.MM.DD HH:mm:ss}</green> - <level>{level}</level>: {message}",
    level=loglevel
)

logger.info("Populating data structure from content of spotify/YourLibrary.json")
with open("spotify/YourLibrary.json", 'r') as file:
    library = json.load(file)

    for artist in library['artists']:
        addArtist(artist['name'], spotify_uri=artist['uri'], inLibrary=True)
    for album in library['albums']:
        addAlbum(album['album'], album['artist'],
                 spotify_uri=album['uri'], inLibrary=True)
    for track in library['tracks']:
        addTrack(track['track'], track['album'],
                 track['artist'], spotify_uri=track['uri'], inLibrary=True)

logger.info("Populating data structure from content of spotify/Playlist1.json")
with open("spotify/Playlist1.json", 'r') as file:
    for playlist in getPlaylists(json.load(file)['playlists']):
        for item in playlist['items']:
            addTrack(item['trackName'], item['albumName'],
                     item['artistName'], spotify_uri=item['spotify_uri'], inLibrary=True)

with open('data.json', 'w') as file:
    file.write(json.dumps(data, indent=2))

spotify = Spotify()

for artist in data:
    if completeArtist or getArtist(artist)['inLibrary']:
        spotify_uri = getArtist(artist)['spotify_uri']
        downloadURI.append(
            spotify_uri if spotify_uri is not None else spotify.getURI(artist=artist))
        continue
    for album in getArtist(artist)['albums']:
        if completeAlbum or getAlbum(artist, album)['inLibrary']:
            spotify_uri = getAlbum(artist, album)['spotify_uri']
            downloadURI.append(
                spotify_uri if spotify_uri is not None else spotify.getURI(artist=artist, album=album))
            continue
        for track in getAlbum(artist, album)['tracks']:
            if getTrack(artist, album, track)['inLibrary']:
                # TODO I'm pretty confident to say that if a traks ends up here, it's in the library
                spotify_uri = getTrack(artist, album, track)['spotify_uri']
                downloadURI.append(spotify_uri if spotify_uri is not None else spotify.getURI(
                    artist=artist, album=album, track=track))

with open('uri.lst', 'w') as file:
    file.write("\n".join(downloadURI))