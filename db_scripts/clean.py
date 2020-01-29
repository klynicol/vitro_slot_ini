from base import *

"""
@author Mark Wickline 2020-01-29
Runs periodically to clean up unecessary database entries and files.
"""


qry = """
SELECT * FROM jobs
WHERE datedone_dat NOTNULL
AND datedone_dat NOT LIKE 'Error%'
    """
jobs = conn.query_db(qry)

for job in jobs:
    #remove the run file if it exits
    filePath = prodPath + job['jobname_txt'] + ".vmj"
    if os.path.exists(filePath):
        os.remove(filePath)

#remove the entries from the database
conn.query_commit("""
DELETE FROM jobs
WHERE datedone_dat NOTNULL
AND datedone_dat NOT LIKE 'Error%'
""")

conn.close()

result = {
    'status' : True,
    'message' : 'jobs removed'
}
print(json.dumps(result))