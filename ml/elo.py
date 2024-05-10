import sqlite3

class ELO:
    def __init__(self, fighters): 
        self.__initialize_elos(fighters)
        self.K = 32

    def print_scores(self):
        sorted_by_elo = sorted(self.fighters.items(), key=lambda x: x[1]['elo'])
        for fighter in sorted_by_elo:
            print(fighter[1]['elo'], fighter[1]['name'])

    def update_elos(self, winner, loser):
        w_elo = self.fighters[winner]['elo']
        l_elo = self.fighters[loser]['elo']
        pwbl = self.prob_x_beats_y(winner, loser)
        plbw = self.prob_x_beats_y(loser, winner)

        self.fighters[winner]['elo'] = round(w_elo + self.K*(1 - pwbl))
        self.fighters[loser]['elo'] = round(l_elo - self.K*(1 - plbw))

    def prob_x_beats_y(self, x, y):
        x_elo = self.fighters[x]['elo']
        y_elo = self.fighters[y]['elo']
        return 1/(1 + 10**((y_elo - x_elo)/400))
    
    def __initialize_elos(self, fighters):
        self.fighters = {}
        for fighter in fighters:
            self.fighters[fighter[0]] = {'name': fighter[1], 'elo': 1500}


def get_fighters(curs):
    query = "SELECT id, name FROM Fighters"
    curs.execute(query)
    results = curs.fetchall()
    return results

def get_fights(curs):
    query = """SELECT fighter1, fighter2, winner 
               FROM Fights 
               WHERE winner IS NOT NULL
               ORDER BY date ASC"""
    curs.execute(query)
    results = curs.fetchall()
    return results

if __name__ == '__main__':
    conn = sqlite3.connect('fight.db')
    curs = conn.cursor()

    fighters = get_fighters(curs)
    fights = get_fights(curs)

    elos = ELO(fighters)
    for fight in fights:
        winner = fight[2]
        if fight[0] == winner:
            loser = fight[1]
        else:
            loser = fight[0]

        elos.update_elos(winner, loser)

    elos.print_scores()

    curs.close()
    conn.close()
