from base import *

"""
@author Mark Wickline 12/16/19
Query all jobs for a specific order number
"""

jobName = fields.getvalue('jobName')

result = conn.query_db(
	"SELECT * FROM jobs WHERE jobname_txt LIKE '{name}%'".format(name=jobName))
conn.close()
print(json.dumps(result))