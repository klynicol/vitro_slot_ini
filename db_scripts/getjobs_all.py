from base import *

"""
@author Mark Wickline 2020-01-16
Get's all the jobs that have not been completed.
This should be everything Vitro Mark has the potential to run in it's que.
"""

result = conn.query_db(
    """
	SELECT *
    FROM `jobs`
    WHERE
    datedone_dat IS NULL
    """
)
conn.close()
print(json.dumps(result))