import spotipy
from operator import itemgetter
import os
import spotipy.util as util
from statistics import mean
import spotipy.oauth2 as oauth2
import data
import pprint

# authorization
def generate_unauthorised_token():

    auth = oauth2.SpotifyClientCredentials(
        client_id=os.environ.get('SPOTIPY_CLIENT_ID'),
        client_secret=os.environ.get('SPOTIPY_CLIENT_SECRET'))
    token = auth.get_access_token()
    return token

# useful shortcut to convert song_id to name - artist(s)
def convert_song_id(song_id, dictionary):

    return " - ".join([dictionary[song_id]['name'],
                       dictionary[song_id]['artists']])


# analysis
def song_distance(id_song1, id_song2, dictionary):
    """Determine how similar/dissimilar songs are"""
    item_1, item_2 = dictionary[id_song1], dictionary[id_song2]

    name_1, artists_1 = item_1['name'], item_1['artists']
    name_2, artists_2 = item_2['name'], item_2['artists']

    if name_1 == name_2 and any(artist in artists_1 for artist in artists_2):
        return 0

    # data of both songs
    key_1, mode_1, valence_1, energy_1 = item_1['key'], item_1['mode'], item_1['valence'], item_1['energy']
    key_2, mode_2, valence_2, energy_2 = item_2['key'], item_2['mode'], item_2['valence'], item_2['energy']

    # set distance to -1 if key of either song cannot be detected
    if key_1 == -1 or key_2 == -1:
        distance = -1

    # distance function between songs: use 'modular distance' between key_1 and key_2
    key_distance = min([abs(key_1 - x)
                        for x in [key_2, key_2 + 12, key_2 - 12]])

    ''' multiplicative constants below can be chosen freely, but larger multiplier
    for key_distance works best'''
    distance = 15 * key_distance + 5 * \
        abs(mode_1 - mode_2) + abs(valence_1 -
                                   valence_2) + abs(energy_1 - energy_2)

    return distance


def similar_dissimilar_song_pairs(dictionary):
    distances = []
    song_ids = list(dictionary.keys())
    for i, track_1 in enumerate(song_ids):
        for track_2 in song_ids[i + 1:]:
            distances.append(
                [song_distance(track_1, track_2, dictionary), track_1, track_2])

    dist, track_1, track_2 = min(distances)

    duplicates = []
    while dist == 0 or dist == -1:

        name = dictionary[track_1]['name']
        artists = dictionary[track_1]['artists']
        duplicates.append([name, artists])

        distances.remove([0, track_1, track_2])
        dist, track_1, track_2 = min(distances)

    if duplicates != []:
        print(f'The following tracks appear more than once (with different spotify ids):')

        printed = []
        for name, artists in duplicates:
            if [name, artists] in printed:
                continue
            print(f'\t - {name} by {artists}')
            printed.append([name, artists])

        print("These pairs of tracks are trivially the most similar, and are therefore ignored \n")

    pair_similar = min(distances)[1:]
    pair_different = max(distances)[1:]

    similar_1, similar_2 = [convert_song_id(
        x, dictionary) for x in pair_similar]
    different_1, different_2 = [convert_song_id(
        x, dictionary) for x in pair_different]

    print(f'Two most similar songs are {similar_1} and {similar_2}')
    print(f'Two most dissimilar songs are {different_1} and {different_2} \n')

    return distances


def rearrange(track_ids, dictionary, distances):
    '''takes in dictionary,
    return ordered list of track_ids such that song_distance is minimised '''

    # candidates of form (distance, start, finish)
    candidates = sorted(distances, reverse=True)[:8]

    mean_dist = mean([d[0] for d in distances])

    d = {}
    for index, id_1 in enumerate(track_ids):
        # name_1 = dictionary[id_1]['name']
        d[id_1] = [[id_2, song_distance(id_1, id_2, dictionary)]
                   for id_2 in track_ids if id_2 != id_1]

    for dist, start, finish in candidates:

        current_max = dist
        current_res = track_ids
        current_mean = mean_dist

        temp = start
        res = [finish, start]
        dists_ = []

        while True:

            # list of id, distance; select those that are not already in res
            trackslist = [(dictionary[id_]['name'], dist_)
                          for (id_, dist_) in d[temp] if id_ not in res]

            if not trackslist:
                break

            id_, dist_ = min([(id_, dist_) for (id_, dist_)
                              in d[temp] if id_ not in res], key=itemgetter(1))

            res.append(id_)
            dists_.append(dist_)

            temp = id_

        finish = res.pop(0)
        res.append(finish)

        if mean(dists_) + max(dists_) < current_mean + current_max:
            current_max = max(dists_)
            current_res = res
            current_dists = dists_

    return current_res


def organise_new_playlist(username, playlist_name, dictionary, track_ids):
    '''
    playlist_name: name of playlist to be rearranged
    dictionary: dictionary of pairs track_id: [track_info]
                where track info contains song name, key, bpm, etc.
    '''

    track_ids = [item[0] for item in track_ids]
    distances = similar_dissimilar_song_pairs(dictionary)
    track_ids = rearrange(track_ids, dictionary, distances)

    new_playlist_name = f'Rearranged | {playlist_name}'
    playlist_description = ''

    # Token
    token = util.prompt_for_user_token(username=username, scope='playlist-modify-public,playlist-modify-private',
                                       client_id=os.environ.get('SPOTIPY_CLIENT_ID'), client_secret=os.environ.get('SPOTIPY_CLIENT_SECRET'),
                                       redirect_uri=os.environ.get('SPOTIPY_REDIRECT_URI'))

    sp = spotipy.Spotify(auth=token)
    sp.trace = False

    new_playlist = sp.user_playlist_create(
        username, new_playlist_name, playlist_description)
    new_playlist_id = new_playlist['id']

    # add tracks to new playlist
    sp.user_playlist_add_tracks(username, new_playlist_id, track_ids)


token = generate_unauthorised_token()
spotify = spotipy.Spotify(auth=token)

username = input('Enter username: ')
playlists = data.get_playlists(username, spotify)

pp = pprint.PrettyPrinter(indent=10, width=3)
print('\n Here are your public playlists: \n')
pprint.pprint(", ".join(list(playlists.keys())))

which_playlist = input('\nEnter the names of the playlist you would like to rearrange: ')

names = which_playlist.split(',')
playlist_ids = [playlists[name] for name in names]

# rearrange
track_ids = data.write_playlist(username, playlist_ids, spotify)
dictionary = data.get_track_data(track_ids, spotify)
organise_new_playlist(username, names[0], dictionary, track_ids)
