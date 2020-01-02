print("Status: 200 OK")
print("Content-Type: application/json")
print('Access-Control-Allow-Origin: *')
print('')
import sqlite3
import cgi
"""
@author Mark Wickline 12/20/2019
This script is capable of assigning jobs from the order tracker
table `vitrodb_slots`.
"""

try:
	conn = sqlite3.connect('job.db')
except Error as e:
	print(e)

fields = cgi.FieldStorage()
jobName = fields.getvalue('job')