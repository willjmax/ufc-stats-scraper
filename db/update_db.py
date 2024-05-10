import requests
import sqlite3
from bs4 import BeautifulSoup
from datetime import datetime
from scrape_fighters import scrape_fighter
from scrape_fights import get_fighter_dob, insert_fight, insert_round, scrape_fight

def event_exists(uuid):
    query = "SELECT * FROM Fights WHERE UUID_UFCSTATS_EVENT='{uuid}'".format(uuid=uuid)
    curs.execute(query)
    if curs.fetchone():
        return True
    else:
        return False

def get_event_uuid(soup):
    table = soup.find('table', {'class': 'b-statistics__table-events'})
    tbody = table.find('tbody')
    trs = tbody.find_all('tr')

    for tr in trs:
        if tr.find('img'):
            continue

        if tr.find('td', {'class', 'b-statistics__table-col_type_clear'}):
            continue

        latest_event = tr
        break

    uuid = latest_event.find('a')['href'].split('/')[4]

    return uuid

def insert(curs, fight, fighter1, fighter2):
    dob1 = get_fighter_dob(curs, fight['fighter1'])
    dob2 = get_fighter_dob(curs, fight['fighter2'])

    timedelta1 = datetime.fromtimestamp(fight['date']) - datetime.fromtimestamp(dob1)
    timedelta2 = datetime.fromtimestamp(fight['date']) - datetime.fromtimestamp(dob2)

    if dob1 == 0:
        fight['age1'] = 0
    else:
        fight['age1'] = timedelta1.days
    if dob2 == 0:
        fight['age2'] = 0
    else:
        fight['age2'] = timedelta2.days

    print('Scraping {event}'.format(event=fight['event']))

    try:
        times = fight['timeformat'].split('-')
        del fight['timeformat']
    except KeyError:
        times = 0

    fightid = insert_fight(curs, fight)
    count=0
    for rnd in fighter1:
        rnd['fight'] = fightid
        try:
            rnd['time'] = times[count]
        except:
            rnd['time'] = 0
        count = count + 1

    count=0
    for rnd in fighter2:
        rnd['fight'] = fightid
        try:
            rnd['time'] = times[count]
        except:
            rnd['time'] = 0
        count = count + 1

    insert_round(curs, fighter1)
    insert_round(curs, fighter2)


def scrape_event(curs, uuid):
    url = 'http://ufcstats.com/event-details/{uuid}'.format(uuid=uuid)
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    table = soup.find('table')
    tbody = table.find('tbody')
    trs = tbody.find_all('tr')

    date = soup.find('li', {'class': 'b-list__box-list-item'}).text.replace('Date:', '').strip()
    date = datetime.strptime(date, '%B %d, %Y').timestamp()

    for tr in trs:
        uuid = tr['onclick'].split('/')[4].replace('\'', '').replace(')', '')
        fight, fighter1, fighter2 = scrape_fight(curs, uuid)
        fight['date'] = date
        insert(curs, fight, fighter1, fighter2)

if __name__ == '__main__':
    conn = sqlite3.connect('fight.db')
    curs = conn.cursor()

    url = 'http://ufcstats.com/statistics/events/completed'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    uuid = get_event_uuid(soup)

    if not event_exists(uuid):
        scrape_event(curs, uuid)


    conn.commit()
    curs.close()
    conn.close()
