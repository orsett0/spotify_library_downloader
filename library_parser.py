#!/usr/bin/env python

import json
import sys
from loguru import logger

logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YY.MM.DD HH:mm:ss}</green> - <level>{level}</level>: {message}",
    level='DEBUG'
)

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


def addArtist(artistName: str, spotify_uri=None, albums=None, inLibrary=False):
    if artistName in data:
        return False

    data[artistName] = {
        'spotify_uri': spotify_uri,
        'inLibrary': inLibrary,
        'albums': {} if albums is None else albums,
    }

    logger.debug(f"addArtist: Added '{artistName}': {json.dumps(data[artistName])}")

    return True


def addAlbum(albumName, artistName, spotify_uri=None, tracks=None, inLibrary=False):
    if not addArtist(artistName) and albumName in data[artistName]['albums']:
        return False

    data[artistName]['albums'][albumName] = {
        'spotify_uri': spotify_uri,
        'inLibrary': inLibrary,
        'tracks': {} if tracks is None else tracks,
    }

    logger.debug(f"addAlbum: In '{artistName}',\t added '{albumName}': {json.dumps(data[artistName]['albums'][albumName])}")

    return True


def addTrack(trackName, albumName, artistName, spotify_uri=None, inLibrary=False):
    if not addAlbum(albumName, artistName) and trackName in data[artistName]['albums'][albumName]['tracks']:
        return False

    data[artistName]['albums'][albumName]['tracks'][trackName] = {
        'spotify_uri': spotify_uri,
        'inLibrary': inLibrary}

    logger.debug(f"addTrack: In '{artistName}'\t'{albumName}',\t added '{trackName}': {json.dumps(data[artistName]['albums'][albumName]['tracks'][trackName])}")

    return True


def getArtist(artistName):
    return data[artistName]


def getAlbum(albumName, artistName):
    return data[artistName]['albums'][albumName]


def getTrack(trackName, albumName, artistName):
    return data[artistName]['albums'][albumName]['tracks'][trackName]


def getArtists():
    return list(data.keys())


def getAlbums(artistName):
    return list(data[artistName]['albums'].keys())


def getTracks(albumName, artistName):
    return list(data[artistName]['albums'][albumName]['tracks'].keys())

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


def getArtistsFromData(data: list):
    return data['artists']


def getTracksFromData(data: list):
    return data['tracks']


def getAlbumsFromData(data: list):
    return data['albums']


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

with open("spotify/Playlist1.json", 'r') as file:
    for playlist in getPlaylists(json.load(file)['playlists']):
        for item in playlist['items']:
            addTrack(item['trackName'], item['albumName'],
                     item['artistName'], spotify_uri=item['spotify_uri'], inLibrary=True)

with open('data.json', 'w') as file:
    file.write(json.dumps(data, indent=2))
