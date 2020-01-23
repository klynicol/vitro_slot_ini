import requests

'''
@author Mark Wickline 2020-01-14
This is a test script for the connectivity between the slotIni.py
program and order tracker to store slots in the database.

When ready, move this code to the slotIni.py program.
'''

response = requests.post('http://otdev.crystal-d.com/ot/index.php/vitro/saveSlots', data={'something':'somethingValue'})
print(response.content)