import json

# [
    # {
    #     'artist': "artist name",
    #     'spotify_uri': "spotify:artist:uri",
    #     'albums': [
    #         {
    #             'name': "album name",
    #             'spotify_uri': "spotify:album:uri",
    #             'tracks': [
    #                 {
    #                     'track': "track name",
    #                     'spotify_uri': "spotify:track:uri"
    #                 },
    #                 # ...
    #             ]
    #         },
    #         # ...
    #     ]
    # },
#     # ...
# ]
data = []

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
                'artistName': items['track']['artistName']
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

with open("spotify/Playlists1.json") as file:
    for playlist in getPlaylists(json.load(file.read())['playlists']):
        for item in playlist['items']:
            if next((element for element in data if element['artist'] == item['artistName']), None) is None:
                data.append({
                    'artist': item['artistName'],
                    'spotify_uri': None,
                    'albums': [{
                            'name': item['albumName'],
                            'spotify_uri': None,
                            'tracks': [{
                                    'track': item['trackName'],
                                    'spotify_uri': None
                                }]
                        }]
                })
            

# TODO
# Populate data.
