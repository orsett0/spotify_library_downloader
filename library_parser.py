import json

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


def addArtist(artistName: str, spotify_uri=None, albums={}, inLibrary=False):
    if data[artistName] is not None:
        return False

    data[artistName] = {
        'spotify_uri': spotify_uri,
        'albums': albums,
        'inLibrary': inLibrary
    }

    return True


def addAlbum(albumName, artistName, spotify_uri=None, tracks={}, inLibrary=False):
    if not addArtist(artistName) and data[artistName]['albums'][albumName] is not None:
        return False

    data[artistName]['albums'][albumName] = {
        'spotify_uri': spotify_uri,
        'tracks': tracks,
        'inLibrary': inLibrary
    }

    return True


def addTrack(trackName, albumName, artistName, spotify_uri=None, inLibrary=False):
    if not addAlbum(albumName, artistName) and data[artistName]['albums'][albumName]['tracks'][trackName] is not None:
        return False

    data[artistName]['albums'][albumName]['tracks'][trackName] = {
        'spotify_uri': spotify_uri,
        'inLibrary': inLibrary}

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
                'trackName': items['track']['trackName'],
                'albumName': items['track']['albumName'],
                'artistName': items['track']['artistName'],
                'spotify_uri': items['track']['trackUri']
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


with open("spotify/YourLibrary.json", 'r') as file:
    library = json.load(file.read())

    for artist in library['artists']:
        addAlbum(artist['artist'], spotify_uri=artist['uri'], inLibrary=True)
    for album in library['albums']:
        addAlbum(album['album'], album['artist'],
                 spotify_uri=album['uri'], inLibrary=True)
    for track in library['tracks']:
        addTrack(track['track'], track['album'],
                 track['artist'], spotify_uri=track['uri'])

with open("spotify/Playlists1.json", 'r') as file:
    for playlist in getPlaylists(json.load(file.read())['playlists']):
        for item in playlist['items']:
            addTrack(item['trackName'], item['albumName'],
                     item['artistName'], spotify_uri=item['spotify_uri'])
