import requests
import json
import os
from asyncio import sleep
from bs4 import BeautifulSoup

async def update():
    while True:
        if not os.path.exists('data'):
            os.mkdir('data')
        print('Updating database...')
        categories = {'politics':'data/politics.json', 'war':'data/war.json', 'economics/finance':'data/finance.json', 'world':'data/world.json', 'science':'data/science.json', 'techno':'data/techno.json'}
        for category in list(categories.keys()):
            database = []
            try:
                previous = json.loads(open(categories[category], 'r').read())
            except:
                previous = [{'link':None}]
            updated = False
            i = 1
            while (not updated) and i <= 20:
                responce = requests.get(f'https://www.unian.net/{category}?page={i}')
                soup = BeautifulSoup(responce.content, 'html.parser')
                news_set = soup.find_all(class_ = 'list-thumbs__item')
                images = soup.find_all(class_ = 'list-thumbs__image')
                for n in news_set:
                    news_title = ' '.join(n.div.text.split()[:-2])
                    if news_title[-1] == ',':
                        news_title = news_title[:-1]
                    news_link = n.div.a.get('href')
                    news_date = n.div.div.text.split()[1]
                    try:
                        image_link = images[news_set.index(n)].img['data-src']
                    except:
                        image_link = 'none'
                    if news_link == previous[0]['link']:
                        updated = True
                        break
                    database.append({'title':news_title, 'category':category, 'link':news_link, 'date':news_date, 'image':image_link})
                i += 1
                await sleep(1)
            print(database)
            if not previous == [{'link':None}]:
                database.extend(previous)
            with open(categories[category], 'w') as file:
                file.write(json.dumps(database))
        print('Database updated')
        await sleep(3600)