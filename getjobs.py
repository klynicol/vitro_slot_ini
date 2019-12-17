print("Status: 200 OK")
print("Content-Type: application/json")
print('Access-Control-Allow-Origin: *')
print('')
import sqlite3
import cgi # Requests coming in
import json

"""
@author Mark Wickline 12/16/19
Query all jobs for a specific order number
"""
try:
	conn = sqlite3.connect('job.db')
except Error as e:
	print(e)

def query_db(query, args=(), one=False):
    cur = conn.cursor()
    cur.execute(query, args)
    r = [dict((cur.description[i][0], value) \
               for i, value in enumerate(row)) for row in cur.fetchall()]
    cur.connection.close()
    return (r[0] if r else None) if one else r

# c = conn.cursor()
fields = cgi.FieldStorage()
order = fields.getvalue('order')
# qrs = c.execute("SELECT * FROM jobs WHERE jobname_txt LIKE '{order}%'".format(order=order))
result = query_db(
	"SELECT * FROM jobs WHERE jobname_txt LIKE '{order}%'".format(order=order))
print(json.dumps(result))
conn.close()