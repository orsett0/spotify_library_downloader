#!/usr/bin/env python

import json
import sys
import requests
import urllib.parse
import subprocess
import os
import click
from loguru import logger


spotify = None
data = None


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


class Data:

    def __init__(self):
        self.data = {}

    def addArtist(self, artistName: str, spotify_uri=None, albums=None, inLibrary=False) -> bool:
        if artistName in self.getData():
            return False

        self.data[artistName] = {
            'spotify_uri': spotify_uri,
            'inLibrary': inLibrary,
            'albums': {} if albums is None else albums,
        }

        logger.debug(
            f"addArtist: Added '{artistName}': {json.dumps(self.getData()[artistName])}")

        return True

    def addAlbum(self, albumName, artistName, spotify_uri=None, tracks=None, inLibrary=False) -> bool:
        if not self.addArtist(artistName) and albumName in self.getArtist(artistName)['albums']:
            return False

        self.data[artistName]['albums'][albumName] = {
            'spotify_uri': spotify_uri,
            'inLibrary': inLibrary,
            'tracks': {} if tracks is None else tracks,
        }

        logger.debug(
            f"addAlbum: In '{artistName}',\t added '{albumName}': {json.dumps(self.getAlbum(artistName, albumName))}")

        return True

    def addTrack(self, trackName, albumName, artistName, spotify_uri=None, inLibrary=False) -> bool:
        if not self.addAlbum(albumName, artistName) and trackName in self.getAlbum(artistName, albumName)['tracks']:
            return False

        self.data[artistName]['albums'][albumName]['tracks'][trackName] = {
            'spotify_uri': spotify_uri,
            'inLibrary': inLibrary}

        logger.debug(
            f"addTrack: In '{artistName}'\t'{albumName}',\t added '{trackName}': {json.dumps(self.getTrack(artistName, albumName, trackName))}")

        return True

    def getArtist(self, artistName) -> dict:
        return self.data[artistName]

    def getAlbum(self, artistName, albumName) -> dict:
        return self.data[artistName]['albums'][albumName]

    def getTrack(self, artistName, albumName, trackName) -> dict:
        return self.data[artistName]['albums'][albumName]['tracks'][trackName]

    def getData(self) -> dict:
        return self.data


def getPlaylists(data: list) -> dict:
    result = {}
    for playlist in data:
        items = []

        for item in playlist['items']:
            items.append({
                'trackName': item['track']['trackName'],
                'albumName': item['track']['albumName'],
                'artistName': item['track']['artistName'],
                'spotify_uri': item['track']['trackUri']
            })

        result[playlist['name']] = items

    return result


def getURI(artist=None, album=None, track=None) -> str:
    logger.debug(f"Getting URI for {artist} - {album} - {track}")

    spotify_uri = (data.getArtist(artist) if album is None
                   else data.getAlbum(artist, album) if track is None
                   else data.getTrack(artist, album, track))['spotify_uri']

    if spotify_uri is None:
        spotify_uri = spotify.requestURI(artist, album, track)

    return spotify_uri


def checkValidURI(uri: str) -> bool:
    uri = uri.split(":")
    return len(uri) == 3 and uri[0] == 'spotify' and uri[1] in ['artist', 'album', 'track'] and len(uri[2]) == 22


def getURIType(uri: str) -> str | None:
    if not checkValidURI(uri):
        return None

    return uri.split(':')[1]


def askUserForURIs(failed_uri) -> list[str]:
    valid = []
    for failed in failed_uri:
        new_uri = None
        while new_uri is None:
            new_uri = input(
                f"Enter URI for {' - '.join(failed.values())}\n(Leave empty to skip, insert 'all' to skip all): ")

            if new_uri.lower == 'all':
                return valid

            if new_uri == "":
                break

            if not checkValidURI(new_uri):
                logger.error("Invalid URI.")
                new_uri = None

            failed['uri'] = new_uri
            valid.append(failed)
    return valid


def uriFetcher(completeAlbum: bool, completeArtist: bool) -> list[dict]:
    downloadURI = []
    failed_uri = []

    logger.info("Getting URIs of all the elements")

    # TODO this is orrible. i'm confident i could do it better.
    for artist in data.getData():
        if completeArtist or data.getArtist(artist)['inLibrary']:
            spotify_uri = getURI(artist=artist)

            if spotify_uri is None:
                failed_uri.append({
                    'artist': artist})
            else:
                downloadURI.append({
                    'artist': artist,
                    'uri': spotify_uri})

            continue
        for album in data.getArtist(artist)['albums']:
            if completeAlbum or data.getAlbum(artist, album)['inLibrary']:
                spotify_uri = getURI(artist=artist, album=album)

                if spotify_uri is None:
                    failed_uri.append({
                        'album': album,
                        'artist': artist})
                else:
                    downloadURI.append({
                        'artist': artist,
                        'album': album,
                        'uri': spotify_uri})

                continue
            for track in data.getAlbum(artist, album)['tracks']:
                # It should always be in the library if it's present in the data structure, but anyway
                if data.getTrack(artist, album, track)['inLibrary']:
                    spotify_uri = getURI(
                        artist=artist, album=album, track=track)

                    if spotify_uri is None:
                        failed_uri.append({
                            'artist': artist,
                            'album': album,
                            'track': track})
                    else:
                        downloadURI.append({
                            'artist': artist,
                            'album': album,
                            'track': track,
                            'uri': spotify_uri})

    # TODO This part has not been properly tested.
    if len(failed_uri) != 0:
        logger.warning(f'''I was unable to get the URIs for the following elements in your library:
    {chr(10).join(" - ".join(failed.values()) for failed in failed_uri)}''')
        downloadURI += askUserForURIs(failed_uri)

    return downloadURI


def downloadLibrary(downloadURI, output_dir: str) -> None:
    logger.info("Calling freyr-js to download the songs.")

    try:
        os.mkdir("library")
    except FileExistsError:
        pass

    with open("freyr.out", 'a') as out,  open("freyr.err", 'a') as err:

        for uri in downloadURI:
            uri_type = getURIType(uri['uri'])
            logger.info(f"freyr: downloading {uri_type} '{uri[uri_type]}'")

            cmd = ['./freyr-js/freyr.sh', uri['uri'], '--no-bar',
                   '--no-logo', '--no-header', '--no-stats', '-d', output_dir]
            logger.debug(f"executing {' '.join(cmd)}")

            # TODO stderr should be also printed with logger.error
            # Consider also notifying the user if one or more
            # of the songs he has in his library have not been downloaded.
            freyr = subprocess.run(cmd, stdout=out, stderr=err)


def createPlaylists(playlists: dict, lib_dir: str) -> None:
    logger.info("Creating playlists.")

    cwd = os.getcwd()
    for playlist in playlists.keys():
        with open(f"{lib_dir}/{playlist}.m3u8", 'w') as file:
            file.write("#EXTM3U\n")

            for tracks in playlists[playlist]:
                content = os.listdir(
                    f"{lib_dir}/{tracks['artistName']}/{tracks['albumName']}")
                for element in content:
                    if tracks['trackName'] in element:
                        file.write(
                            f"{cwd}/{lib_dir}/{tracks['artistName']}/{tracks['albumName']}/{element}\n")
                        break
                else:
                    logger.error(
                        f"Couldn't find a valid path for {tracks['artistName']} - {tracks['albumName']} - {tracks['trackName']}.")


def uriSorter(URIs: list[dict]) -> list[dict]:
    sorted = []

    uri_IDs = [ uri[getURIType(uri['uri'])] for uri in URIs]
    uri_IDs.sort()

    for id in uri_IDs:
        for uri in URIs:
            if uri[getURIType(uri['uri'])] == id:
                sorted.append(uri)
                break

    return sorted


@click.command()
@click.option(
    "--spotify-data",
    "-d",
    default="./spotify",
    type=click.STRING,
    help="point to a folder containing the files 'YourLibrary.json' and 'Playlist1.json'",
)
@click.option(
    "--output-dir",
    "-o",
    default="./library",
    type=click.STRING,
    help="Directory where to download songs"
)
@click.option(
    "--complete-albums",
    is_flag=True,
    default=False,
    type=click.BOOL,
    help="For every song, downloads the entire album to which it belongs"
)
@click.option(
    "--complete-artist",
    is_flag=True,
    default=False,
    type=click.BOOL,
    help="For every song and album, downloads the entire artist to which it belongs"
)
@click.option(
    "--no-library",
    is_flag=True,
    default=False,
    type=click.BOOL,
    help="Downloads songs only from the playlists"
)
@click.option(
    "--no-playlists",
    is_flag=True,
    default=False,
    type=click.BOOL,
    help="Downloads songs only from your library"
)
@click.option(
    "--only-playlists",
    is_flag=True,
    default=False,
    type=click.BOOL,
    help="Only create playlists with existing songs, do not download"
)
@click.option(
    "--only-download",
    is_flag=True,
    default=False,
    type=click.BOOL,
    help="Downloads only, do not create playlists"
)
@click.option(
    "--debug",
    is_flag=True,
    default=False,
    type=click.BOOL,
)
def main(spotify_data: str, output_dir: str,
         complete_albums: bool, complete_artist: bool,
         no_library: bool, no_playlists: bool,
         only_playlists: bool, only_download: bool,
         debug: bool) -> None:

    global spotify, data

    logger.remove()
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:HH:mm:ss}</green> - <level>{level}</level>: {message}",
        level='DEBUG' if debug else 'INFO'
    )

    data = Data()
    spotify = Spotify()

    logger.info("Populating the data structure...")

    if not no_library:
        database = f"{spotify_data}/YourLibrary.json"

        logger.info(f"Using data in {database}")
        with open(database, 'r') as file:
            library = json.load(file)

        for artist in library['artists']:
            data.addArtist(
                artist['name'], spotify_uri=artist['uri'], inLibrary=True)
        for album in library['albums']:
            data.addAlbum(album['album'], album['artist'],
                          spotify_uri=album['uri'], inLibrary=True)
        for track in library['tracks']:
            data.addTrack(track['track'], track['album'],
                          track['artist'], spotify_uri=track['uri'], inLibrary=True)

    if not no_playlists:
        database = f"{spotify_data}/Playlist1.json"

        logger.info(f"Using data in {database}")
        with open(database, 'r') as file:
            playlists = getPlaylists(json.load(file)['playlists'])

        for playlist in playlists.keys():
            for item in playlists[playlist]:
                data.addTrack(item['trackName'], item['albumName'],
                              item['artistName'], spotify_uri=item['spotify_uri'], inLibrary=True)

    if not only_playlists:
        URIs = uriSorter(uriFetcher(complete_albums, complete_artist))
        downloadLibrary(URIs, output_dir)

    if not only_download and not no_playlists:
        createPlaylists(playlists, output_dir)
        

if __name__ == '__main__':
    main()
