import pickle
import re
import asyncio
import aiohttp
import requests as requests
from bs4 import BeautifulSoup
import time
import os


__all__ = ['filter_movie_div', 'create_edges', 'load_cached', 'save_cached',
           'get_soup', 'parse_description', 'get_actor_name', 'get_movie_html']


def load_cached() -> tuple:
    cached_actors = {}
    cached_movies = {}
    if os.path.isfile('cached_actors.pkl'):
        with open('cached_actors.pkl', 'rb') as file:
            cached_actors = pickle.load(file)
    if os.path.isfile('cached_movies.pkl'):
        with open('cached_movies.pkl', 'rb') as file:
            cached_movies = pickle.load(file)
    return cached_actors, cached_movies


def save_cached(cached: dict, actors: bool = True) -> None:
    path = 'cached_movies.pkl'
    if actors:
        path = 'cached_actors.pkl'
    with open(path, 'wb') as file:
        pickle.dump(cached, file)


class Node:
    def __init__(self, link):
        self.name = str()
        self.link = link
        self.soup = None
        self.edges = None

    def set_soup(self, soup) -> None:
        self.soup = soup

    def get_soup(self, ):
        return BeautifulSoup(self.soup, features="html.parser")

    def set_edges(self, edges):
        self.edges = edges

    def get_edges(self, links=True):
        if links:
            return [edge[1] for edge in self.edges]
        return self.edges

    def __len__(self):
        return len(self.edges)


headers = {
    'Accept-Language': 'en',
    'X-FORWARDED-FOR': '2.21.184.0'
}


async def get_soup(url: str, session=False) -> str:
    if session:
        async with session.get(url, headers=headers,) as response:
            assert response.status == 200
            html = await response.text()
            return html
    else:
        return requests.get(url, headers=headers).text


is_actor = re.compile(r"(actor-\w+)|(actress-\w+)")


def filter_movie_div(div: BeautifulSoup):
    id_is_actor = div.attrs.get('id')
    if not id_is_actor:
        return None
    else:
        id_is_actor = is_actor.findall(id_is_actor)

    if id_is_actor:
        q = re.compile(r'</b>\s\(.+\)\s<br')
        in_production = div.select('.in_production')
        temp = div.decode_contents()
        founded = q.findall(temp)
        if not in_production and not founded:
            return div


async def check(link: str, limit: int, function, session) -> Node:
    node = Node(link)
    response = await get_soup(link, session)
    time.sleep(0.1)
    soup = BeautifulSoup(response, features="html.parser")
    alternative = function(soup, limit)
    node.set_edges(alternative)
    return node


async def create_edges(nodes: list,
                       cashed: dict,
                       visited: list,
                       limit: int,
                       function: object,
                       actor: bool = False) -> tuple:
    async with aiohttp.ClientSession() as session:
        counter = 0
        to_check = []
        checked = []
        edges = []
        cached_counter = 0
        new_counter = 0
        for link in nodes:
            if link in cashed:
                checked.append(cashed[link])
                cached_counter += 1
            else:
                to_check.append(check(link, limit, function, session))
                counter += 1
                new_counter += 1
            if counter > 0 and counter % 10 == 0:
                new_nodes = await asyncio.gather(*to_check)
                checked = checked + new_nodes
                to_check = []
                time.sleep(5)
                counter = 0

        new_nodes = await asyncio.gather(*to_check)

        nodes = checked + new_nodes

        assert len(nodes) == new_counter + cached_counter

        for node in nodes:
            cashed[node.link] = node
            for link in node.get_edges():
                if actor:
                    link = f'{link}fullcredits'
                if link in visited:
                    continue
                visited.add(link)
                edges.append(link)
        return edges, cashed, visited


name = re.compile(r'nm\d*')


def get_actor_name(link):
    return f'https://www.imdb.com/name/{name.findall(link)[0]}/'


def parse_description(text):
    soup = BeautifulSoup(text, features="html.parser")
    return soup.find('span', {'data-testid': 'plot-l'}).text


async def get_movie_html(links):
    async with aiohttp.ClientSession() as session:
        movie_html = await asyncio.gather(
            *[get_soup(link, session) for link in links]
        )
    return movie_html
