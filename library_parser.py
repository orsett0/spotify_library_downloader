#!/usr/bin/env python

import json
import sys
import requests
import urllib.parse
import subprocess
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
completeArtist = True

downloadURI = []
failed_uri = []


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

    def requestURI(self, artist, album=None, track=None):
        logger.debug("Requesting to Spotify.")

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
        except IndexError:
            # IndexError for "L'Officina Della Camomilla".
            # The problem is not caused from " ' ", I tested it.
            # The problem is presente even for some album.
            logger.error(
                f"Cannot get uri for '{artist}' - '{album}' - '{track}'. Do it manually.")
            uri = None

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


def getURI(artist=None, album=None, track=None):
    logger.debug(f"Getting URI for {artist} - {album} - {track}")

    spotify_uri = (getArtist(artist) if album is None
                   else getAlbum(artist, album) if track is None
                   else getTrack(artist, album, track))['spotify_uri']

    if spotify_uri is None:
        spotify_uri = spotify.requestURI(artist, album, track)

    return spotify_uri


def askUserForURIs():
    valid = []

    user_uris = input(
        "You can enter them now in a comma separated list (with no spaces), or leave empty and move on:")

    if len(user_uris) == 0:
        return valid

    for uri in user_uris.split(","):
        check = uri.split(":")

        if len(check) != 3 or check[0] != 'spotify' or check[1] not in ['artist', 'album', 'track'] or len(check[2]) != 22:
            logger.error(f"Invalid uri: {uri}")
        else:
            valid.append(uri)

    if len(valid) != len(user_uris):
        logger.warning("Some URIs you inserted aren't valid.")
        valid += askUserForURIs()

    return valid


logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YY.MM.DD HH:mm:ss}</green> - <level>{level}</level>: {message}",
    level=loglevel
)


logger.info("Populating the data structure...")

logger.info("Using data in spotify/YourLibrary.json")
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

logger.info("Using data in spotify/Playlist1.json")
with open("spotify/Playlist1.json", 'r') as file:
    for playlist in getPlaylists(json.load(file)['playlists']):
        for item in playlist['items']:
            addTrack(item['trackName'], item['albumName'],
                     item['artistName'], spotify_uri=item['spotify_uri'], inLibrary=True)

with open('data.json', 'w') as file:
    file.write(json.dumps(data, indent=2))


logger.info("Getting URIs of all the elements")

spotify = Spotify()

# TODO this is orrible. i'm confident i could do it better.
for artist in data:
    if completeArtist or getArtist(artist)['inLibrary']:
        spotify_uri = getURI(artist=artist)

        if spotify_uri is None:
            failed_uri.append({'artist': artist})
        else:
            downloadURI.append(spotify_uri)

        continue
    for album in getArtist(artist)['albums']:
        if completeAlbum or getAlbum(artist, album)['inLibrary']:
            spotify_uri = getURI(artist=artist, album=album)

            if spotify_uri is None:
                failed_uri.append({'artist': artist, 'album': album})
            else:
                downloadURI.append(spotify_uri)

            continue
        for track in getAlbum(artist, album)['tracks']:
            # It should always be in the library if it's present in the data structure, but anyway
            if getTrack(artist, album, track)['inLibrary']:
                spotify_uri = getURI(artist=artist, album=album, track=track)

                if spotify_uri is None:
                    failed_uri.append(
                        {'artist': artist, 'album': album, 'track': track})
                else:
                    downloadURI.append(spotify_uri)

# TODO The "ask user" part has not been tested.
logger.warning(f'''I was unable to get the URIs for the following elements in your library:
{chr(10).join(" - ".join(failed.values()) for failed in failed_uri)}''')
downloadURI += askUserForURIs()

with open('uri.lst', 'w') as file:
    file.write("\n".join(downloadURI))
