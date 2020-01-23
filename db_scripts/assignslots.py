from base import *
conn = Connect()

"""
@author Mark Wickline 2020-01-22

Assign slots from the vitro laser grid module.
"""

tool = fields.getvalue('tool')
cell = fields.getvalue('cell')
ordernr = fields.getvalue('ordernr')

conn.query_db(
'''
    UPDATE `jobs`
    SET
    `dateslot_date` = NOW(),
    `unit_txt` = '{}',
    `slot_txt` = '{}'
    WHERE `ordernr_txt` = '{}'
'''.format(tool, cell, ordernr)
)
print(json.dumps({"status": True}))