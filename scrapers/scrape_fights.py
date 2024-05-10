import re
import requests
import sqlite3
from bs4 import BeautifulSoup
from datetime import datetime

def fight_exists(curs, uuid):
    query = "SELECT * FROM Fights WHERE UUID_UFCSTATS='{uuid}'".format(uuid=uuid)
    curs.execute(query)
    if curs.fetchone():
        return True
    else:
        return False

def fighter_exists(curs, uuid):
    query = "SELECT * FROM Fighters WHERE UUID_UFCSTATS='{uuid}'".format(uuid=uuid)
    curs.execute(query)
    if curs.fetchone():
        return True
    else:
        return False

def get_division(bout):
    if 'Strawweight' in bout or '115 LBS' in bout:
        return 'Strawweight'
    if 'Flyweight' in bout or '125 LBS' in bout:
        return 'Flyweight'
    if 'Bantamweight' in bout or '135 LBS' in bout:
        return 'Bantamweight'
    if 'Featherweight' in bout or '145 LBS' in bout:
        return 'Featherweight'
    if 'Lightweight' in bout or '155 LBS' in bout:
        return 'Lightweight'
    if 'Welterweight' in bout or '170 LBS' in bout:
        return 'Welterweight'
    if 'Middleweight' in bout or '185 LBS' in bout:
        return 'Middleweight'
    if 'Light Heavyweight' in bout or '205 LBS' in bout:
        return 'Light Heavyweight'
    if 'Heavyweight' in bout or '265 LBS' in bout:
        return 'Heavyweight'
    if 'Catch Weight' in bout or 'Catchweight' in bout:
        return 'Catchweight'

    return 'Other'

def get_fighters(curs):
    query = "SELECT id, UUID_UFCSTATS, name FROM Fighters"
    curs.execute(query)
    results = curs.fetchall()
    return results

def get_fighter_dob(curs, fighter):
    query = "SELECT dob FROM Fighters WHERE id={fighter}".format(fighter=fighter)
    curs.execute(query)
    results = curs.fetchone()[0]
    return results

def get_fighter_count(curs):
    query = "SELECT COUNT(*) FROM Fighters"
    curs.execute(query)
    results = curs.fetchone()[0]
    return results

def get_fighter_id(curs, uuid_ufcstats):
    query = "SELECT id FROM Fighters WHERE UUID_UFCSTATS='{uuid}'".format(uuid=uuid_ufcstats)
    curs.execute(query)
    results = curs.fetchone()[0]
    return results

def scrape_fighters_and_winner(curs, soup, fight):
    fighters = soup.find('div', {'class': 'b-fight-details__persons'})
    first = True
    for fighter in fighters.find_all('div', {'class': 'b-fight-details__person'}):
        fighter_uuid = fighter.find('a')['href'].split('/')[4]

        if not fighter_exists(curs, fighter_uuid):
            fighter = scrape_fighter(curs, fighter_uuid)
            cols = "(name, nickname, dob, height, reach, UUID_UFCSTATS)"
            vals = "('{name}', '{nickname}', {dob}, {height}, {reach}, '{uuid}')".format(name=fighter['name'], nickname=fighter['nickname'], dob=fighter['dob'], height=fighter['height'], reach=fighter['reach'], uuid=fighter['uuid'])
            query = "INSERT INTO Fighters {cols} VALUES {vals}".format(cols=cols, vals=vals)
            curs.execute(query)

        if first:
            fight['fighter1'] = get_fighter_id(curs, fighter_uuid)
            first = False
        else:
            fight['fighter2'] = get_fighter_id(curs, fighter_uuid)

        outcome = fighter.find('i').text.strip()
        if outcome == 'W':
            fight['winner'] = get_fighter_id(curs, fighter_uuid)
        if outcome == 'NC':
            fight['no_contest'] = True
        else:
            fight['no_contest'] = False
        if outcome == 'D':
            fight['draw'] = True
        else:
            fight['draw'] = False

    return fight

def scrape_fight_details(soup, fight):
    div = soup.find('div', {'class': 'b-fight-details__fight'})

    if div.find('img', {'src': 'http://1e49bc5171d173577ecd-1323f4090557a33db01577564f60846c.r80.cf1.rackcdn.com/perf.png'}):
        fight['perf'] = True
    else:
        fight['perf'] = False

    if div.find('img', {'src': 'http://1e49bc5171d173577ecd-1323f4090557a33db01577564f60846c.r80.cf1.rackcdn.com/fight.png'}):
        fight['fotn'] = True
    else:
        fight['fotn'] = False

    if div.find('img', {'src': 'http://1e49bc5171d173577ecd-1323f4090557a33db01577564f60846c.r80.cf1.rackcdn.com/belt.png'}):
        fight['title'] = True
    else:
        fight['title'] = False

    bout = div.find('i', {'class': 'b-fight-details__fight-title'}).text
    if 'Women' in bout:
        fight['gender'] = 'F'
    else:
        fight['gender'] = 'M'

    fight['division'] = get_division(bout)

    div = soup.find('div', {'class': 'b-fight-details__content'})
    first = True
    for p in div.find_all('p', {'class': 'b-fight-details__text'}):
        if first:
            for i in p.find_all('i', {'class': ['b-fight-details__text-item_first', 'b-fight-details__text-item']}):
                text = i.text.replace('\n', '').strip()

                if 'Method:' in text:
                    text = text.replace('Method:', '').strip()
                    fight['win_method'] = text
                if 'Round:' in text:
                    text = text.replace('Round:', '').strip()
                    fight['end_round'] = int(text)
                if 'Time:' in text:
                    text = text.replace('Time:', '').strip()
                    mins, secs = text.split(':')
                    fight['end_time'] = int(mins)*60 + int(secs)
                if 'Time format:' in text:
                    text = text.replace('Time format:', '').strip()
                    timeformat = re.search('\([0-9-]*\)', text)
                    if timeformat:
                        fight['rounds'] = len(timeformat.group(0).split('-'))
                        fight['timeformat'] = timeformat.group(0).replace('(', '').replace(')', '')
                    else:
                        fight['rounds'] = 0


                if 'Referee:' in text:
                    text = text.replace('Referee:', '').strip()
                    fight['referee'] = text

            first = False
        else:
            text = p.text.replace('\n', '').strip()
            text = text.replace('Details:', '').strip()
            fight['win_details'] = text.replace(' ', '')

    return fight

def scrape_totals_per_round(soup):
    labels = ['knockdowns', 'sig_strikes', 'sig_strike_accuracy', 'total_strikes', 'takedowns', 'takedown_accuracy', 'submission_attempts', 'reversals', 'control_time']
    fighter1 = []
    fighter2 = []

    try:
        table = soup.find_all('table', {'class': 'b-fight-details__table'})[0]
    except IndexError:
        return [],[] 
    except Exception as e:
        print(e)

    round_count = 0 
    for tr in table.find_all('tr', {'class': 'b-fight-details__table-row'}):
        if tr.find('th'): continue

        fighter1.append({})
        fighter2.append({})
        fighter1[round_count]['round'] = round_count + 1
        fighter2[round_count]['round'] = round_count + 1
        
        cell_count = 0
        for td in tr.find_all('td', {'class': 'b-fight-details__table-col'}):
            ### skip names
            if 'l-page_align_left' in td['class']: continue

            first = True
            for p in td.find_all('p', {'class': 'b-fight-details__table-text'}):
                if first:
                    fighter1[round_count][labels[cell_count]] = p.text.strip()
                    first = False
                else:
                    fighter2[round_count][labels[cell_count]] = p.text.strip()


            cell_count = cell_count + 1
        round_count = round_count + 1

    return fighter1, fighter2

def scrape_strikes_per_round(soup, fighter1, fighter2):
    labels = ['sig_strikes', 'sig_strike_accuracy', 'head_strikes', 'body_strikes', 'leg_strikes', 'distance_strikes', 'clinch_strikes', 'ground_strikes']

    try:
        table = soup.find_all('table', {'class': 'b-fight-details__table'})[1]
    except IndexError:
        return fighter1, fighter2
    except Exception as e:
        print(e)

    round_count = 0
    for tr in table.find_all('tr', {'class': 'b-fight-details__table-row'}):
        if tr.find('th'): 
            continue
        
        cell_count = 0
        for td in tr.find_all('td', {'class': 'b-fight-details__table-col'}):
            ### skip names
            if 'l-page_align_left' in td['class']: 
                continue

            first = True
            for p in td.find_all('p', {'class': 'b-fight-details__table-text'}):
                if first:
                    fighter1[round_count][labels[cell_count]] = p.text.strip()
                    first = False
                else:
                    fighter2[round_count][labels[cell_count]] = p.text.strip()

            cell_count = cell_count + 1
        round_count = round_count + 1
    return fighter1, fighter2

def scrape_fight(curs, uuid):
    url = "http://ufcstats.com/fight-details/{uuid}".format(uuid=uuid)
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    fighter1 = {}
    fighter2 = {}
    fight = {}
    fight['UUID_UFCSTATS'] = uuid

    h2 = soup.find('h2')
    event_uuid = h2.find('a')['href'].split('/')[4]
    fight['UUID_UFCSTATS_EVENT'] = event_uuid

    h2 = soup.find('h2', {'class': 'b-content__title'})
    fight['event'] = h2.text.strip()

    fight = scrape_fighters_and_winner(curs, soup, fight)
    fight = scrape_fight_details(soup, fight)

    fighter1, fighter2 = scrape_totals_per_round(soup)
    fighter1, fighter2 = scrape_strikes_per_round(soup, fighter1, fighter2)

    for rnd in fighter1:
        rnd['fighter'] = fight['fighter1']

    for rnd in fighter2:
        rnd['fighter'] = fight['fighter2']

    fighter1 = parse_fighter_fields(fighter1)
    fighter2 = parse_fighter_fields(fighter2)

    return fight, fighter1, fighter2

def parse_fighter_fields(fighter):
    tmp = {}

    for rnd in fighter:
        for key in rnd.keys():
            if key == 'fighter':
                continue

            if type(rnd[key]) != str:
                continue

            if '%' in rnd[key]:
                rnd[key] = int(rnd[key].replace('%', ''))
                continue
            if ':' in rnd[key]:
                mins, secs = rnd[key].split(':')
                rnd[key] = int(mins)*60 + int(secs)
                continue
            if 'of' in rnd[key]:
                landed, attempted = rnd[key].split('of')
                rnd[key] = int(landed.strip())
                tmp[key + '_attempted'] = int(attempted.strip())
                continue
            if '---' in rnd[key]:
                rnd[key] = 0

        rnd = (rnd | tmp)  

    return fighter

def scrape_fights_from_fighter(curs, uuid):
    url = "http://ufcstats.com/fighter-details/{uuid}".format(uuid=uuid)
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    tbody = soup.find('tbody', {'class': 'b-fight-details__table-body'})
    for tr in tbody.find_all('tr', {'class': 'b-fight-details__table-row'}):
        button = tr.find('a')

        # skip upcoming fight
        if button.text == 'next':
            continue

        url = button['href']
        uuid = url.split('/')[4]
        date = tr.find_all('p', {'class': 'b-fight-details__table-text'})[12].text.strip()
        date = datetime.strptime(date, '%b. %d, %Y').timestamp()

        # fight may have been added when scraping other fighter
        if fight_exists(curs, uuid):
            continue

        fight, fighter1, fighter2 = scrape_fight(curs, uuid) 
        fight['date'] = int(date)

        dob1 = get_fighter_dob(curs, fight['fighter1'])
        dob2 = get_fighter_dob(curs, fight['fighter2'])

        timedelta1 = datetime.fromtimestamp(int(date)) - datetime.fromtimestamp(dob1)
        timedelta2 = datetime.fromtimestamp(int(date)) - datetime.fromtimestamp(dob2)

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

def insert_fight(curs, fight):
    cols = str(tuple(fight.keys()))
    vals = str(tuple([fight[x] for x in fight.keys()]))
    query = "INSERT OR IGNORE INTO Fights {cols} VALUES {vals}".format(cols=cols, vals=vals)
    curs.execute(query)

    return curs.lastrowid

def insert_round(curs, fighter):
    for rnd in fighter:
        cols = str(tuple(rnd.keys()))
        vals = str(tuple([rnd[x] for x in rnd.keys()]))
        query = "INSERT INTO Rounds {cols} VALUES {vals}".format(cols=cols, vals=vals)
        curs.execute(query)

if __name__ == '__main__':
    conn = sqlite3.connect('fight.db')
    curs = conn.cursor()

    fighters = get_fighters(curs)
    #fighters = [(1759, '07f72a2a7591b409', 'Jon Jones')]
    fighters_count = get_fighter_count(curs)
    count = 1
    for fighter in fighters:
        print("({count}/{total}) {name}".format(count=count, total=fighters_count, name=fighter[2]))
        scrape_fights_from_fighter(curs, fighter[1])
        count = count + 1

    conn.commit()
    curs.close()
    conn.close()
