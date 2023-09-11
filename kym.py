#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Knowyourmeme.com definitions scraper.
"""

import requests
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
import sqlite3
import time

SEARCH_SIMILARITY_THRESHOLD = .4

HEADERS = {'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36')}
 
 
def search_meme(text):
    """Return a meme name and url from a meme keywords.
    """
    r = requests.get('http://knowyourmeme.com/search?q=%s' % text, headers=HEADERS)
    soup = BeautifulSoup(r.text, 'html.parser')
    memes_list = soup.find(class_='entry_list')
    if memes_list:
        meme_path = memes_list.find('a', href=True)['href']
        return meme_path.replace('-', ' '), 'https://knowyourmeme.com%s' % meme_path
    return None, None
 
 
def search(text):
    """Return a meme definition from a meme keywords.
    """
    meme_name, url = search_meme(text)
    if meme_name and SequenceMatcher(None, text, meme_name).ratio() >= SEARCH_SIMILARITY_THRESHOLD:
        r = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(r.text, 'html.parser')
        entry = soup.find('h2', {'id': 'about'})
        return '%s' % (entry.next.next.next.text)
 
 
conn = sqlite3.connect('memes.db')
cursor = conn.cursor()
cursor.execute(''' CREATE TABLE IF NOT EXISTS memes (id INTEGER PRIMARY KEY, title TEXT, meaning TEXT) ''')
conn.commit()
 
for page_num in range(1, 2278):
    url = f'https://knowyourmeme.com/memes/all/page/{page_num}?sort=oldest'
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')
 
    #Find and process the titles
    h2s = soup.find_all("h2")
    for h2 in h2s:
        title = h2.a.text.strip()
        try:
            meaning = search(title)
            if meaning:
                print(f'Meme: {title}')
                print(f'Meaning: {meaning}')
                print('-' * 50)

                cursor.execute('INSERT INTO memes (title, meaning) VALUES (?,?)',(title, meaning))
                conn.commit()
        except Exception as e:
            print(f"Error processing meme '{title}': {str(e)}")

    time.sleep(1)

conn.close()
