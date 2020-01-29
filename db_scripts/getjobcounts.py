from base import *

"""
@author Mark Wickline 2019-12-26
Get all the jobs in the job DB and groups them by job name
so we can count how many jobs are on each order.
"""


qry = '''
SELECT COUNT(id_txt) as count, jobname_txt as jobname
FROM jobs
GROUP BY jobname_txt
'''
result = conn.query_db(qry)
conn.close()
print(json.dumps(result))