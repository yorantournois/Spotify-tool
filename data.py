import spotipy.oauth2 as oauth2
import os

def generate_unauthorised_token():

    auth = oauth2.SpotifyClientCredentials(
        client_id=os.environ.get('SPOTIPY_CLIENT_ID'),
        client_secret=os.environ.get('SPOTIPY_CLIENT_SECRET'))
    token = auth.get_access_token()
    return token


def get_playlists(username, spotify):

    playlists = spotify.user_playlists(username)
    playlist_dict = {}
    number_tracks = 0
    for playlist in playlists['items']:

        number_tracks += playlist['tracks']['total']
        playlist_dict[playlist['name']] = playlist['id']

    return playlist_dict


def write_tracks(tracks, spotify):

    track_ids = []
    while True:
        for item in tracks['items']:
            track = item['track']

            try:
                track_id = track['id']
                track_name = track['name']
                track_artists = ', '.join([artists['name']
                                           for artists in track['artists']])
                track_popularity = track['popularity']
                track_ids.append(
                    [track_id, track_name, track_artists, track_popularity])

            except KeyError:
                name = track['name']
                print(f'Skipping the track "{name}"')

        if tracks['next']:
            tracks = spotify.next(tracks)
        else:
            break

    return track_ids


def write_playlist(username, playlist_ids, spotify):

    track_ids = []

    for id_ in playlist_ids:
        results = spotify.user_playlist(
            username, id_, fields='tracks, next, name')
        tracks = results['tracks']
        track_ids.extend(write_tracks(tracks, spotify))

    return track_ids


def get_track_data(track_ids, spotify):

    dictionary = {}
    for track_id, name, artists, popularity in track_ids:

        if not track_id:
            continue

        features = spotify.audio_features(track_id)
        item = features[0]
        key, mode, bpm, valence, energy = item['key'], item['mode'], round(
            item['tempo']), item['valence'], item['energy']

        ''' no overcounting of tracks, but beware that the same song
        may appear in different albums; they'll have a different id'''

        dictionary[track_id] = {'name': name, 'artists': artists, 'key': key,
                                'mode': mode, 'bpm': bpm, 'valence': valence,
                                'energy': energy, 'popularity': popularity}

    return dictionary


# useful shortcut to convert song_id to name - artist(s)
def convert_song_id(song_id, dictionary):

    return " - ".join([dictionary[song_id]['name'],
                       dictionary[song_id]['artists']])
