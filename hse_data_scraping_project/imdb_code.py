# define helper functions if needed
# and put them in `imdb_helper_functions` module.
# you can import them and use here like that:
import time

from bs4 import BeautifulSoup
from imdb_helper_functions import *
from urllib.parse import urljoin
import math

import asyncio

__all__ = ['get_actors_by_movie_soup',
           'get_movies_by_actor_soup',
           'get_movie_distance',
           'get_movie_descriptions_by_actor_soup'
           ]


LINK_START = 'https://www.imdb.com/'
MAX_DISTANCE = 3


def get_actors_by_movie_soup(
        cast_page_soup: BeautifulSoup,
        num_of_actors_limit: int = None
) -> list:
    actors = []
    images = cast_page_soup.find('table', {'class': 'cast_list'})
    images = images.find_all('img', limit=num_of_actors_limit)
    for item in images:
        name_of_actor = item.get('title', None)
        if name_of_actor:
            link = urljoin(LINK_START, item.parent.attrs["href"])
            actors.append((name_of_actor, link))
    return actors


def get_movies_by_actor_soup(
        actor_page_soup,
        num_of_movies_limit=None
) -> list:
    title_and_link = []
    film_cat = actor_page_soup.find('div', {'id': 'filmography'})
    films = film_cat.find_all(
        filter_movie_div,
        limit=num_of_movies_limit
    )
    for film in films:
        name = film.a.text
        link = urljoin(LINK_START, film.a.attrs['href'])
        title_and_link.append((name, link))
    return title_and_link


def get_movie_distance(
        actor_start_url,
        actor_end_url,
        num_of_actors_limit=None,
        num_of_movies_limit=None
):
    cached_actors, cached_movies = load_cached()
    cached_act_l, cached_mov_l = len(cached_actors), len(cached_movies)

    actor_start_url = get_actor_name(actor_start_url)
    actor_end_url = get_actor_name(actor_end_url)
    print(actor_start_url, actor_end_url)
    visited_movies = set()
    visited_actors = set()
    current_distance = 1
    actors_queue = [actor_start_url]

    while actors_queue or movies_queue:
        edges = asyncio.run(
            create_edges(actors_queue,
                         cached_actors,
                         visited_movies,
                         num_of_movies_limit,
                         get_movies_by_actor_soup,
                         True)
        )
        movies_queue, cached_actors, visited_movies = edges
        if len(cached_actors) > cached_act_l:
            save_cached(cached_actors, True)
            cached_act_l = len(cached_actors)

        edges = asyncio.run(
            create_edges(movies_queue,
                         cached_movies,
                         visited_actors,
                         num_of_actors_limit,
                         get_actors_by_movie_soup)
        )

        actors_queue, cached_movies, visited_actors = edges
        if len(cached_movies) > cached_mov_l:
            save_cached(cached_movies, False)
            cached_mov_l = len(cached_movies)

        if actor_end_url in actors_queue:
            save_cached(cached_actors, True)
            save_cached(cached_movies, False)
            time.sleep(2)
            return current_distance
        current_distance += 1
        if current_distance > MAX_DISTANCE:
            return math.inf
    return math.inf


def get_movie_descriptions_by_actor_soup(actor_page_soup):
    movies = get_movies_by_actor_soup(
        actor_page_soup,
        num_of_movies_limit=None
    )
    links = [i[1] for i in movies]
    movie_html = asyncio.run(get_movie_html(links))
    descriptions = [parse_description(text) for text in movie_html]
    return descriptions

if __name__ == '__main__':

    soup = asyncio.run(get_soup('https://www.imdb.com/name/nm0010010'))
    soup = BeautifulSoup(soup)
    description = get_movie_descriptions_by_actor_soup(soup)
    print(len(description))