import aiohttp
import asyncio
from bs4 import BeautifulSoup
import json
import matplotlib.pyplot as plt
import numpy as np
import re
import time

start = time.perf_counter()
movies = []

def get_pages(baseUrl):
    pages = []
    for index in range(1, 50):
        pages.append(f'{baseUrl}page/{index}/')

    return pages

async def get_links_on_pages(session, url):
    async with session.get(url) as response:
        page = await response.text()
        bs =    BeautifulSoup(page,'lxml')
        headers= bs.find_all('h2', {'class': 'post-title'})
        page_links = [header.a['href'] for header in headers]
        return page_links

async def get_all_genres(pages):
    links_list = []
    genres = []
    timeout = aiohttp.ClientTimeout(total = 600)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for page in pages:
            links_list.append(asyncio.ensure_future(get_links_on_pages(session, page)))
        links_list = await asyncio.gather(*links_list)
        links = [link for sublist in links_list  for link in sublist]

        for link in links:
            genres.append(asyncio.ensure_future(get_movie_genres(session, link)))
        genres = await asyncio.gather(*genres)

        flat_genres = [genre for sublist in genres for genre in sublist]
        return count_genres(flat_genres)

def count_genres(genres):
    genres_count = {}
    for genre in genres:
        if  genre  in genres_count:
            genres_count[genre ] += 1
        else: genres_count[genre] = 1

    '''file = open('movies_db.json', 'a')
    file.write(json.dumps(genres_count))
    file.close()'''
    return genres_count


async def get_movie_genres(session, url):
    async with session.get(url) as response:
        html = await response.text()
        bs = BeautifulSoup(html, 'lxml')
        name = bs.find('span', {'itemprop': 'name'}).get_text()
        movie_name = re.split(r'[1900-2070]', name)[0].strip()

        if movie_name in movies: return []
        movies.append(movie_name)
        entry_text = bs.find('div', {'class': 'entry'}).get_text()
        genre_line = re.search(r'\(Genres\).*\((.*)\)', entry_text)
        if genre_line == None: return ''
        genre_line = genre_line.group(1)
        genres = [genre.strip() for genre in genre_line.split(',')]
        return genres

def create_pie_chart(movie_dict):
    genres = movie_dict.keys()
    values = [movie_dict[genre] for genre in genres]
    y = np.array(values)
    plt.pie(y, labels = genres)
    plt.legend()
    plt.title('Classification of Movies on a movie website(tfpdl.se) \n based on their genres')
    plt.show()

pages = get_pages('http://tfpdl.se/category/movies/')
movie_genres = asyncio.run(get_all_genres(pages))
elapsed = time.perf_counter()-start

create_pie_chart(movie_genres)
print(f'returned {len(movies)} in {elapsed: 0.2f} seconds')