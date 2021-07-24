from imdb_code import *
from imdb_helper_functions import get_soup
import math
import pandas as pd
import asyncio
from bs4 import BeautifulSoup
import os

def write_description(item):
    name = '_'.join(item[0].split(' '))
    file_name = f'data/{name}.txt'
    exist = os.path.isfile(file_name)
    if not exist:
        url = item[1]
        full_url = f'https://www.imdb.com/name/{url}/'
        print(full_url, name, url)
        html_text = asyncio.run(get_soup(full_url))
        soup = BeautifulSoup(html_text, features="html.parser")
        text = get_movie_descriptions_by_actor_soup(soup)
        file_name = f'data/{name}.txt'
        exist = os.path.isfile(file_name)
        with open(f'data/{name}.txt', 'w') as file:
            file.write(' '.join(text))


def get_all_distances(actor_dict, actors_limit, movies_limit, path, reflex):
    values = list(actor_dict.values())
    l = len(actor_dict)
    matrix = [[0 for _ in range(l)] for _ in range(l)]
    for i in range(l):
        k = 0 if reflex else i
        for j in range(k, l):
            actor_from = values[i]
            actor_to = values[j]
            if actor_from == actor_to:
                matrix[i][j] = 0
                continue
            distance = get_movie_distance(
                            actor_start_url=actor_from,
                            actor_end_url=actor_to,
                            num_of_actors_limit=actors_limit,
                            num_of_movies_limit=movies_limit
            )
            prev = matrix[i][j]
            if prev < distance and prev > 0:
                 continue
            matrix[i][j] = distance if distance < math.inf else 0
            matrix[j][i] = distance if distance < math.inf else 0
    return matrix


def create_csv(matrix, keys, path):
    to_write = []
    names = ['\n'.join(i.split(' ')) for i in keys]
    names = [f'"{i}"' for i in names]
    to_write.append(f",{','.join(names)}")
    for index, key in enumerate(keys):
        to_str = [str(i) for i in matrix[index]]
        row = [names[index], *to_str]
        to_write.append(','.join(row))
    with open(path, 'w') as file:
        file.write('\n'.join(to_write))




if __name__ == "__main__":
    actors_limit = 5
    movies_limit = 5
    path = 'data/matrix.csv'
    actor_dict = {
        'Dwayne Johnson': 'nm0425005',
        'Chris Hemsworth': 'nm1165110',
        'Robert Downey Jr': 'nm0000375',
        'Akshay Kumar': 'nm0474774',
        'Jackie Chan': 'nm0000329',
        'Bradley Cooper': 'nm0177896',
        'Adam Sandler': 'nm0001191',
        'Scarlett Johansson': 'nm0424060',
        'Sofia Vergara': 'nm0005527',
        'Chris Evans': 'nm0262635',
    }
#     m1 = get_all_distances(actor_dict, actors_limit, movies_limit, path, False)
#     m2 = get_all_distances(actor_dict, actors_limit, movies_limit, path, True)
#
#     matrix = [[0, 2, 2, 0, 3, 3, 3, 2, 3, 2],
#               [2, 0, 1, 3, 3, 1, 3, 1, 2, 1],
#               [2, 1, 0, 0, 0, 1, 2, 1, 3, 1],
#               [0, 3, 0, 0, 0, 0, 0, 0, 0, 0],
#               [3, 3, 0, 0, 0, 0, 0, 0, 3, 0],
#               [3, 1, 1, 0, 0, 0, 3, 1, 2, 1],
#               [3, 3, 2, 0, 0, 3, 0, 2, 2, 3],
#               [2, 1, 1, 0, 0, 1, 2, 0, 3, 1],
#               [3, 2, 3, 0, 3, 2, 2, 3, 0, 2],
#               [2, 1, 1, 0, 0, 1, 3, 1, 2, 0]]
#
#     create_csv(m1, actor_dict.keys(), 'data/matrix1.csv')
#     create_csv(m2, actor_dict.keys(), 'data/matrix2.csv')
    for item in actor_dict.items():
        write_description(item)

