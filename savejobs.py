print("Status: 200 OK")
print("Content-Type: application/json")
print('Access-Control-Allow-Origin: *')
print('')
import sqlite3
import requests # Requests going out
import cgi # Requests coming in
import sys
import shutil
import re
import time
import string
import random
import json
"""
@author Mark Wickline 12/13/19
This script creates jobs in the vitro database for an order.
There's a bug in python that prevents getting JSON data from cgi.FieldStorage()
https://bugs.python.org/issue27777
I could not get sys.stdin.read() to do anything but spin so I'm implimenting any
loops in the calling class and this script will act on a single job.
"""

def randomString(length=3):
    pool = string.ascii_lowercase
    return ''.join(random.choice(pool) for i in range(length))

response = {
	"glassX" : None,
	"glassY" : None,
	"glassZ" : None
}
prodPath = "\\\\Ice9-ProdFile\\3D\\Common-3D\\PRODUCTION\\AIR - NEW - V2"

try:
	conn = sqlite3.connect('job.db')
except Error as e:
	print(e)


fields = cgi.FieldStorage()

# jobName = order number
jobName = fields.getvalue('name')
qty = int(fields.getvalue('qty'))
glass = fields.getvalue('glass')
artNum = fields.getvalue('art')
# vmj path so we know where to grab the file from to stick it into the DB folder.
vmjPath = fields.getvalue('path')
vmjPath = vmjPath.split('AIR - NEW - V2')[1]
vmjPath = vmjPath.replace("\"", "")
vmjPath = prodPath + vmjPath

jobHash = randomString()

# Extract the glass x and y from the file
vmj = open(vmjPath, mode="r", errors='ignore')
for line in vmj:
	if response['glassX'] and response['glassY'] and response['glassZ']:
		break
	if re.match(r'^GLASS_X ', line):
		response['glassX'] = float(line.split('=')[1].strip())
	if re.match(r'^GLASS_Y ', line):
		response['glassY'] = float(line.split('=')[1].strip())
	if re.match(r'^GLASS_Z ', line):
		response['glassZ'] = float(line.split('=')[1].strip())

# Begin creating the jobs.
def createJob(name, index = None, add = None):
	db = conn.cursor()
	date = time.strftime('%Y-%m-%d %H:%M:%S')
	orderName = name + "_" + artNum + "_" + jobHash
	if index:
		orderName += "_" + str(index)
	shutil.copy(
		vmjPath, prodPath + "\\DB SAVES\\" + orderName + ".vmj")
	qry = "INSERT INTO jobs "
	qry += "(ordernr_txt, jobname_txt, add_txt, glas_txt, size_txt, datecreate_dat, user_txt) "
	qry += "VALUES ('{order}', '{name}', '{add}', '{glass}', '{size}', '{date}', '{user}')".format(
		order=orderName,
		name=name + "_" + artNum + "_" + jobHash,
		add=add,
		glass=glass,
		size=str(round(response['glassX'])) + "/" + str(round(response['glassY'])) + "/" + str(round(response['glassZ'])),
		date=date,
		user='savejobs')
	db.execute(qry)

if qty > 1:
	for x in range(qty):
		createJob(jobName, x + 1, "({x}/{qty})".format(x=x + 1, qty=qty))
else: # We only need to create one job
	createJob(jobName)

conn.commit()
print(json.dumps(response))