import spotipy
import matplotlib
import numpy as np
import matplotlib.pyplot as plt
import math
from statistics import mean
from collections import Counter
import spotipy.oauth2 as oauth2
import data
import os

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

    key_1, mode_1, valence_1, energy_1 = item_1['key'], item_1['mode'], item_1['valence'], item_1['energy']
    key_2, mode_2, valence_2, energy_2 = item_2['key'], item_2['mode'], item_2['valence'], item_2['energy']

    # set distance to -1 if key of either song cannot be detected
    # later, select these distances out
    if key_1 == -1 or key_2 == -1:
        distance = -1

    # 'distance' function between songs using 'modular distance' between key_1 and key_2
    key_distance = min([abs(key_1 - x)
                        for x in [key_2, key_2 + 12, key_2 - 12]])
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
        # These pairs of tracks are trivially the most similar, and are therefore ignored
        print(f'The following tracks appear more than once (with different spotify ids):')

        printed = []
        for name, artists in duplicates:
            if [name, artists] in printed:
                continue
            print(f'\t - {name} by {artists}')
            printed.append([name, artists])

    pair_similar = min(distances)[1:]
    pair_different = max(distances)[1:]

    similar_1, similar_2 = [convert_song_id(
        x, dictionary) for x in pair_similar]
    different_1, different_2 = [convert_song_id(
        x, dictionary) for x in pair_different]

    print(f'Two most similar songs are {similar_1} and {similar_2}')
    print(f'Two most dissimilar songs are {different_1} and {different_2} \n')

    return distances


# def valency(dictionary):

#     avg_valence = mean([item['valence'] for item in dictionary.values()])

#     happiest_song, max_valence = max(
#         [(key, value['valence']) for key, value in dictionary.items()], key=itemgetter(1))
#     saddest_song, min_valence = min(
#         [(key, value['valence']) for key, value in dictionary.items()], key=itemgetter(1))

#     if max_valence >= 0.5:
#         print(
#             f'The happiest song is {convert_song_id(happiest_song,dictionary)} ({max_valence})')
#     else:
#         print('''The playlist doesn't have any happy songs!''')

#     if min_valence <= 0.5:
#         print(
#             f'The saddest song is {convert_song_id(saddest_song,dictionary)} ({min_valence})\n')
#     else:
#         print('''The playlist doesn't have any sad songs!\n''')


def popularity(dictionary, plot_histogram=False):

    # most_popular_song, max_popularity = max(
    #     [(key, value['popularity']) for key, value in dictionary.items()], key=itemgetter(1))
    # least_popular_song, min_popularity = min(
    #     [(key, value['popularity']) for key, value in dictionary.items()], key=itemgetter(1))

    # avg_popularity = mean([item['popularity'] for item in dictionary.values()])
    songs_by_popularity = [(value['popularity'], key)
                           for key, value in dictionary.items()]
    data = [item[0] / 10 for item in songs_by_popularity]

    plt.hist(data, rwidth=0.5, align='left', range=(0, 10))
    plt.xlabel("Popularity")
    plt.ylabel("Number of songs")
    plt.savefig("popularity.pdf")


# def compare_key_frequencies(dictionary):
#     keys = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
#     scales = {i: key for i, key in enumerate(keys)}
#     modes = {0: 'major', 1: 'minor'}

#     average_key_frequencies = {
#         'G major': 0.107, 'C major': 0.102, 'D major': 0.087, 'A major': 0.061,
#         'Db major': 0.006, "F major": 0.053, 'A minor': 0.048, 'Ab major': 0.043,
#         'E minor': 0.042, 'B minor': 0.042, 'E major': 0.042, 'Bb major': 0.042,
#         'Bb minor': 0.032, 'F minor': 0.03, 'F# major': 0.027, 'B major': 0.026,
#         'G minor': 0.026, 'D minor': 0.026, 'F# minor': 0.025, 'Eb major': 0.024,
#         'C minor': 0.024, 'Db minor': 0.021, 'Ab minor': 0.012, 'Eb minor': 0.009
#     }

#     playlist_key_mode_pairs = [(item['key'], item['mode'])
#                                for item in dictionary.values()]
#     playlist_key_mode_pairs = [
#         f'{scales[x]} {modes[y]}' for x, y in playlist_key_mode_pairs]

#     playlist_frequencies = {key: value / sum(Counter(playlist_key_mode_pairs).values(
#     )) for key, value in Counter(playlist_key_mode_pairs).items()}

#     # might have some missing keys: set missing key frequencies to 0
#     for key in average_key_frequencies:
#         playlist_frequencies[key] = playlist_frequencies.get(key, 0)

#     # Analyze the set of differences of frequencies
#     comparison_key_frequencies = sorted([(100 * abs(playlist_frequencies[key] - average_key_frequencies[key]), key)
#                                          for key in playlist_frequencies.keys()], reverse=True)


def plot_keys(dictionary):
    """Plot keys in playlist on camelot wheel"""
    keys = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
    scales = {i: key for i, key in enumerate(keys)}
    modes = {0: 'major', 1: 'minor'}

    playlist_key_mode_pairs = [(item['key'], item['mode'])
                               for item in dictionary.values()]
    key_counter = [f'{scales[x]} {modes[y]}' for x,
                   y in playlist_key_mode_pairs]
    wedge_size = [30] * 12

    # colors
    colors_outer = plt.cm.rainbow(np.linspace(1, 0, 12), 1)
    colors_inner = plt.cm.rainbow(np.linspace(1, 0, 12), 1)

    # colors_center=plt.cm.rainbow(np.linspace(avg_valence,1,1),1)
    max_key_count = max(set(Counter(key_counter).values()))

    # set opacity of key,mode to #count(key,mount)/max
    for i, data in enumerate(colors_outer):
        data[3] = Counter(key_counter)[
            f'{scales[i]} {modes[0]}'] / max_key_count

    for i, data in enumerate(colors_inner):
        data[3] = Counter(key_counter)[
            f'{scales[i]} {modes[1]}'] / max_key_count

    fig, ax = plt.subplots()
    ax.axis('equal')

    mypie, _ = ax.pie(wedge_size, radius=1.4, labeldistance=0.825,
                      colors=colors_inner, startangle=75)
    plt.setp(mypie, width=0.4, edgecolor='black')

    mypie2, _ = ax.pie(wedge_size, radius=1.2 - 0.2,
                       labeldistance=0.75, colors=colors_outer, startangle=75)
    plt.setp(mypie2, width=0.4, edgecolor='black')

    for i in range(12):
        plt.text(0.8 * np.cos(2 * math.pi * (i - 2) / 12), - 0.8 * np.sin(2 * math.pi * (i - 2) / 12),
                 f'{i+1}A', ha='center', va='center', alpha=1, family='sans-serif', fontweight='ultralight')

    for i in range(12):
        plt.text(1.15 * np.cos(2 * math.pi * (i - 2) / 12), - 1.2 * np.sin(2 * math.pi * (i - 2) / 12),
                 f'{i+1}B', ha='center', va='center', alpha=1, family='sans-serif', fontweight='ultralight')

    plt.savefig("keys.pdf")


def visualise_valence_energy(dictionary):
    scatter_data = [(key, 10 * value['valence'], 10 * value['energy'])
                    for key, value in dictionary.items()]
    keys, valences, energies = zip(*scatter_data)

    cmap = matplotlib.cm.get_cmap('plasma')
    normalize = matplotlib.colors.Normalize(vmin=0, vmax=10)

    colors = [cmap(normalize(value)) for value in valences]

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(valences, energies, color=colors)
    ax.set_xlabel("Valence")
    ax.set_ylabel("Energy")

    cax, _ = matplotlib.colorbar.make_axes(ax)
    cbar = matplotlib.colorbar.ColorbarBase(cax, cmap=cmap, norm=normalize)
    cbar.ax.hlines([min(valences) / 10, max(valences) / 10,
                    mean(valences) / 10], 0, 1, colors='w')
    plt.savefig("valence.pdf")


def analyse(dictionary):

    similar_dissimilar_song_pairs(dictionary)

    popularity(dictionary, plot_histogram=True)

    plot_keys(dictionary)

    visualise_valence_energy(dictionary)


token = generate_unauthorised_token()
spotify = spotipy.Spotify(auth=token)

username = input('Enter username: ')
playlists = data.get_playlists(username, spotify)

print('\n Your public playlists: \n')
print(", ".join(list(playlists.keys())))

which_playlist = input('''\nEnter the name of the playlist you would like to analyse,
    or enter 'all' to analyse all playlists: ''')

if which_playlist == 'all':
    playlist_ids = list(playlists.values())
else:
    names = which_playlist.split(',')
    playlist_ids = [playlists[name] for name in names]

track_ids = data.write_playlist(username, playlist_ids, spotify)
dictionary = data.get_track_data(track_ids, spotify)

print(f'Analysing {len(dictionary.keys())} songs in your playlist(s)... \n')

analyse(dictionary)
