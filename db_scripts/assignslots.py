from base import *
conn = Connect()

"""
@author Mark Wickline 2020-01-22

Assign slots from the vitro laser grid module.
"""

tool = fields.getvalue('tool')
cell = fields.getvalue('cell')
ordernr = fields.getvalue('ordernr')


cursor = conn.conn.cursor()
cursor.execute(
'''
    UPDATE `jobs`
    SET
    `dateslot_dat` = datetime('now'),
    `unit_txt` = '{unit}',
    `slot_txt` = '{slot}'
    WHERE `ordernr_txt` = '{ord}'
'''.format(unit=tool, slot=cell, ord=ordernr)
)
conn.conn.commit()
cursor.connection.close()
print(json.dumps({
	"status": True,
	"data" : {
		"ordernr" : ordernr,
		"cell" : cell,
		"tool" : tool
	}
}))