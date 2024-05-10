import sqlite3

def build_schema():
    tables = {
        'Fighters': {
            'id': {'type': 'INTEGER', 'constraint': 'PRIMARY KEY ASC'},
            'name': {'type': 'TEXT'},
            'nickname': {'type': 'TEXT'},
            'dob': {'type': 'INTEGER'},
            'height': {'type': 'REAL'},
            'reach': {'type': 'REAL'},
            'UUID_UFCSTATS': {'type': 'TEXT', 'constraint': 'UNIQUE'}
            },

        'Fights': {
            'id': {'type': 'INTEGER', 'constraint': 'PRIMARY KEY ASC'},
            'fighter1': {'type': 'INTEGER'},
            'fighter2': {'type': 'INTEGER'},
            'rounds': {'type': 'INTEGER'},
            'division': {'type': 'TEXT'},
            'gender': {'type': 'TEXT'},
            'end_round': {'type': 'INTEGER'},
            'end_time': {'type': 'INTEGER'},
            'win_method': {'type': 'TEXT'},
            'win_details': {'type': 'TEXT'},
            'winner' : {'type': 'INTEGER'},
            'draw': {'type': 'INTEGER', 'constraint': 'CHECK(draw IN (0, 1))'},
            'no_contest': {'type': 'INTEGER', 'constraint': 'CHECK(no_contest IN (0, 1))'},
            'title': {'type': 'INTEGER', 'constraint': 'CHECK(no_contest IN (0, 1))'},
            'perf': {'type': 'INTEGER', 'constraint': 'CHECK(no_contest IN (0, 1))'},
            'fotn': {'type': 'INTEGER', 'constraint': 'CHECK(no_contest IN (0, 1))'},
            'referee': {'type': 'TEXT'},
            'event': {'type': 'TEXT'},
            'age1': {'type': 'INTEGER'},
            'age2': {'type': 'INTEGER'},
            'date': {'type': 'INTEGER'},
            'UUID_UFCSTATS': {'type': 'TEXT', 'constraint': 'UNIQUE'},
            'UUID_UFCSTATS_EVENT': {'type': 'TEXT'}
        },

        'Rounds': {
            'id': {'type': 'INTEGER', 'constraint': 'PRIMARY KEY ASC'},
            'fight': {'type': 'INTEGER'},
            'fighter': {'type': 'INTEGER'},
            'round': {'type': 'INTEGER'},
            'time': {'type': 'INTEGER'},
            'sig_strikes': {'type': 'INTEGER'}, 
            'sig_strikes_attempted': {'type': 'INTEGER'},
            'sig_strike_accuracy': {'type': 'INTEGER'}, 
            'total_strikes': {'type': 'INTEGER'}, 
            'total_strikes_attempted': {'type': 'INTEGER'},
            'knockdowns': {'type': 'INTEGER'},
            'takedowns': {'type': 'INTEGER'}, 
            'takedowns_attempted': {'type': 'INTEGER'},
            'takedown_accuracy': {'type': 'INTEGER'}, 
            'submission_attempts': {'type': 'INTEGER'}, 
            'reversals': {'type': 'INTEGER'}, 
            'control_time': {'type': 'INTEGER'},
            'head_strikes': {'type': 'INTEGER'}, 
            'head_strikes_attempted': {'type': 'INTEGER'},
            'body_strikes': {'type': 'INTEGER'}, 
            'body_strikes_attempted': {'type': 'INTEGER'},
            'leg_strikes': {'type': 'INTEGER'}, 
            'leg_strikes_attempted': {'type': 'INTEGER'},
            'distance_strikes': {'type': 'INTEGER'}, 
            'distance_strikes_attempted': {'type': 'INTEGER'},
            'clinch_strikes': {'type': 'INTEGER'}, 
            'clinch_strikes_attempted': {'type': 'INTEGER'},
            'ground_strikes': {'type': 'INTEGER'},
            'ground_strikes_attempted': {'type': 'INTEGER'}
        }
    }

    foreign_keys = {
        'Fights': [('fighter1', 'Fighters(id)'),
                   ('fighter2', 'Fighters(id)'),
                   ('winner', 'Fighters(id)'),
                  ],

        'Rounds': [('fight', 'Fights(id)'),
                   ('fighter', 'Fighters(id)')
                  ]
    }

    return tables, foreign_keys

def build_db(curs, tables, foreign_keys):
   for table in tables.keys():
        create = "CREATE TABLE IF NOT EXISTS {}".format(table)
        cols = []
        fkeys = []

        for key, value in tables[table].items():
            if 'constraint' in value.keys():
                col = "{} {} {}".format(key, value['type'], value['constraint'])
            else:
                col = "{} {}".format(key, value['type'])
            cols.append(col) 

        if table in foreign_keys.keys():
            for fkey in foreign_keys[table]:
                fkeys.append('FOREIGN KEY({}) REFERENCES {}'.format(fkey[0], fkey[1]))
                
        col_str = ','.join(cols)
        fkey_str = ','.join(fkeys)
        strings = [col_str, fkey_str]
        strings = [x for x in strings if x] ## filter out empty strings

        query = create + " ({})".format(','.join(strings))
        curs.execute(query) 

if __name__ == '__main__':
    conn = sqlite3.connect('fight.db')
    curs = conn.cursor()

    tables, foreign_keys = build_schema()
    build_db(curs, tables, foreign_keys)
    conn.commit()

    curs.close()
    conn.close()
