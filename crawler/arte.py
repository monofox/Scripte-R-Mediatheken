import requests
import os.path
import json
import time
import threading

os.makedirs('arte/', exist_ok=True)

TOKEN = 'Bearer Nzc1Yjc1ZjJkYjk1NWFhN2I2MWEwMmRlMzAzNjI5NmU3NWU3ODg4ODJjOWMxNTMxYzEzZGRjYjg2ZGE4MmIwOA'
URL = 'https://api.arte.tv/api/opa/v3/videos?channel=DE'

def write(page, resp):
	with open(os.path.join('arte', 'arte_{:0>3d}.json'.format(page)), 'w', encoding='utf-8') as f:
		f.write(json.dumps(resp))

	print('Saved page {:d}'.format(page))

def fetch(url):
	header = {
		'Authorization': TOKEN
	}
	r = requests.get(url, headers=header)
	print(r.status_code)
	resp = r.json()
	page = resp['meta']['videos']['page']
	print('Fetched page {:d}'.format(page))
	threading.Thread(target=write, kwargs={'page': page, 'resp': resp}).start()

	return resp

#url = URL
url = 'https://api.arte.tv/api/opa/v3/videos?page=1&limit=100&channel=DE'
resp = fetch(url)
#while True and 1==2:
#	resp = fetch(url)
#	url = resp['meta']['videos']['links']['next']['href']
#	time.sleep(0.2)

