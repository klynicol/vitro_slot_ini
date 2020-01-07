print("Status: 200 OK")
print("Content-Type: application/json")
print('Access-Control-Allow-Origin: *')
print('')
import sqlite3
import cgi
import json
"""
@author Mark Wickline 12/20/2019
This script deletes order names from the database. if there are multiple
orders with the same name, it will be deleted.
"""

try:
	conn = sqlite3.connect('job.db')
except Error as e:
	print(e)

fields = cgi.FieldStorage()
jobName = fields.getvalue('job')
c = conn.cursor()

qry = """
    SELECT `ordernr_txt`
    FROM `jobs`
    WHERE `jobname_txt` = '{jobName}'
    """.format(
        jobName = jobName
    )
c.execute(qry)

qry = """
    DELETE FROM `jobs`
    WHERE `jobname_txt` = '{jobName}'
    """.format(
        jobName = jobName)

c.execute(qry)
conn.commit()
result = {
    'qry' : qry
}
print(json.dumps(result))