print("Status: 200 OK")
print("Content-Type: application/json")
print('Access-Control-Allow-Origin: *')
print('')
import sqlite3
import cgi
import json
"""
@author Mark Wickline 12/26/19
Get all the jobs in the job DB and groups them by job name
so we can count how many jobs are on each order.
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

qry = '''
SELECT COUNT(id_txt) as count, jobname_txt as jobname
FROM jobs
GROUP BY jobname_txt
'''
result = query_db(qry)
print(json.dumps(result))