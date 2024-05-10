import requests
import sqlite3
import string
from bs4 import BeautifulSoup
from datetime import datetime
from utils import escape_quotes, monthToNum


def scrape_fighter_uuids():
    alphabet = list(string.ascii_lowercase)
    url = 'http://ufcstats.com/statistics/fighters?char={}&page=all'

    uuids = []
    for i in alphabet:
        pageurl = url.format(i)
        response = requests.get(pageurl)
        soup = BeautifulSoup(response.content, 'html.parser')
        fighters = soup.find_all('tr', {'class': 'b-statistics__table-row'})
        for fighter in fighters:
            fighterurl = fighter.find('a', {'class': 'b-link'})
            if not fighterurl:
                continue
            tds = fighter.find_all('td')
            uuid = fighterurl['href'].split('/').pop().strip()
            uuids.append(uuid)

    return uuids

def scrape_fighter(uuid):
    url = 'http://ufcstats.com/fighter-details/{uuid}'.format(uuid=uuid)
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    fighter = {}
    fighter['uuid'] = uuid

    name = soup.find('span', {'class': 'b-content__title-highlight'}).text.strip()
    nickname = soup.find('p', {'class': 'b-content__Nickname'}).text.strip()

    fighter['name'] = escape_quotes(name)
    fighter['nickname'] = escape_quotes(nickname)

    stat_div = soup.find('ul', {'class': 'b-list__box-list'})

    for li in stat_div.find_all('li'):
        text = li.text.strip().replace('\n', '').replace(' ', '').lower()
        if 'height' in text:
            text = text.replace('height:', '').replace('"', '')
            if text == '--':
                fighter['height'] = 0
            else:
                feet, inches = text.split("'")
                height = int(feet)*12 + int(inches)
                fighter['height'] = height

        if 'reach' in text:
            text = text.replace('reach:', '').replace('"', '')
            if text == '--':
                fighter['reach'] = 0
            else:
                reach = int(text)
                fighter['reach'] = reach

        if 'stance' in text:
            stance = text.replace('stance:', '')
            fighter['stance'] = stance

        if 'dob' in text:
            text = text.replace('dob:', '')
            if text == '--':
                fighter['dob'] = 0
            else:
                monthday, year = text.split(',')
                month, day = monthday[:-2], monthday[-2:]
                dob = int(datetime(int(year), monthToNum(month), int(day)).timestamp())
                fighter['dob'] = dob
       

    return fighter

if __name__ == '__main__':
    uuids = scrape_fighter_uuids()
    fighters = []
    for uuid in uuids:
        fighter = scrape_fighter(uuid)
        fighters.append(fighter)

    conn = sqlite3.connect('fight.db')
    curs = conn.cursor()

    for fighter in fighters:
        cols = "(name, nickname, dob, height, reach, UUID_UFCSTATS)"
        vals = "('{name}', '{nickname}', {dob}, {height}, {reach}, '{uuid}')".format(name=fighter['name'], nickname=fighter['nickname'], dob=fighter['dob'], height=fighter['height'], reach=fighter['reach'], uuid=fighter['uuid'])
        query = "INSERT INTO Fighters {cols} VALUES {vals}".format(cols=cols, vals=vals)
        curs.execute(query)
        conn.commit()

    curs.close()
    conn.close()
