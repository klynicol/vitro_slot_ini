from base import *

"""
@author Mark Wickline 2020-01-05
Query all jobs for a specific order number
"""

jobName = fields.getvalue('jobName')

result = conn.query_db(
    '''
    SELECT 
        *, 
        COUNT(id_txt) AS count,
        COALESCE((SELECT 
            COUNT(id_txt)
            FROM jobs
            WHERE jobname_txt LIKE '{name}%'
            AND slot_txt IS NOT NULL
            GROUP BY jobname_txt),0) AS slots_assigned
        FROM jobs
        WHERE jobname_txt LIKE '{name}%'
        GROUP BY jobname_txt
    '''.format(name=jobName)
)
conn.close()

print(json.dumps(result))