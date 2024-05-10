import pandas as pd
import sqlite3
from sklearn.linear_model import LogisticRegression

def get_data():
    conn = sqlite3.connect('fight.db')
    query = """SELECT fighter1, fighter2, age1, age2, winner
               FROM Fights
               WHERE winner IS NOT NULL
               AND win_method != 'DQ'
               AND age1 != 0
               AND age2 != 0"""

    df = pd.read_sql_query(query, conn)
    df['difference'] = (df.age1 - df.age2).abs()
    df['older'] = df[['age1', 'age2']].max(axis=1)

    df['outcome'] = 0
    df.loc[(df.winner == df.fighter1) & (df.age1 > df.age2), 'outcome'] = 1
    df.loc[(df.winner == df.fighter2) & (df.age2 > df.age1), 'outcome'] = 1
    df.loc[df.age1 == df.age2, 'outcome'] = 1

    return df

def train(df, cols):
    x = df[cols]
    y = df.outcome

    logreg = LogisticRegression(solver='liblinear')
    logreg.fit(x, y)

    return logreg

if __name__ == '__main__':
    df = get_data()

    model = train(df, ['older', 'difference'])

    test = pd.DataFrame([[12045, 1]], columns=['older', 'difference'])
    print('33 vs 33', model.predict_proba(test))
    test = pd.DataFrame([[12045, 1825]], columns=['older', 'difference'])
    print('33 vs 28', model.predict_proba(test))
    test = pd.DataFrame([[14600, 1825]], columns=['older', 'difference'])
    print('40 vs 35', model.predict_proba(test))
    test = pd.DataFrame([[14600, 4380]], columns=['older', 'difference'])
    print('40 vs 28', model.predict_proba(test))
