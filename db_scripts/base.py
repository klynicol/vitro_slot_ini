print("Status: 200 OK")
print("Content-Type: application/json")
print('Access-Control-Allow-Origin: *')
print('')
import sqlite3
import cgi # Requests coming in
import json

'''
@author Mark Wickline 2020-01-21
Acts as a base for all vitro DB API scripts.
'''

class Connect:
    conn = None
    cursor = None
    def __init__(self):
        try:
            self.conn = sqlite3.connect('job.db')
        except sqlite3.Error as e:
            print(e)

    def query_db(self, query, args=(), one=False):
        self.cursor = self.conn.cursor()
        self.cursor.execute(query, args)
        r = [dict((self.cursor.description[i][0], value) \
                for i, value in enumerate(row)) for row in self.cursor.fetchall()]
        self.cursor.connection.close()
        return (r[0] if r else None) if one else r

fields = cgi.FieldStorage()
conn = Connect()