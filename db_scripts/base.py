print("Status: 200 OK")
print("Content-Type: application/json")
print('Access-Control-Allow-Origin: *')
print('')
import sqlite3
import cgi # Requests coming in
import json
import os

'''
@author Mark Wickline 2020-01-21
Acts as a base for all vitro DB API scripts.
'''
fields = cgi.FieldStorage()
prodPath = "\\\\Ice9-ProdFile\\3D\\Common-3D\\PRODUCTION\\AIR - NEW - V2\\DB SAVES\\"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "job.db")

class Connect:
    conn = None
    cursor = None
    def __init__(self):
        try:
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print(e)

    def query_db(self, query, args=(), one=False):
        self.cursor.execute(query, args)
        r = [dict((self.cursor.description[i][0], value) \
                for i, value in enumerate(row)) for row in self.cursor.fetchall()]
        return (r[0] if r else None) if one else r
    def query_commit(self, query):
        self.cursor.execute(query)
        self.conn.commit()
    def close(self):
        self.cursor.connection.close()


conn = Connect()