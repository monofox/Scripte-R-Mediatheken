import urllib.request
import multiprocessing
import json
import time
import datetime
import time
import sys
import threading
import requests
import logging

API_URL = 'https://api.ardmediathek.de/public-gateway?variables={variables}&extensions={extensions}'
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
sh.setLevel(logging.DEBUG)
logger.addHandler(sh)

class ArdFilm(object):

	def __init__(self, id):
		self._id = id
		self._availableTo = None
		self._broadcastOn = None
		self._duration = 0
		self._sender = ''
		self._topic = ''
		self._title = ''
		self._hasSubtitle = False
		self._geoBlocked = None
		self._blockedByFsk = False
		self._channel = ''
		self._contentId = 0
		self._links = []

		showVars = {
			'client': 'ard',
			'clipId': self._id,
			'deviceType': 'pc'
		}
		var = json.dumps(showVars, separators=(',', ':'))
		showExt = {'persistedQuery':{'version':1,'sha256Hash':'a9a9b15083dd3bf249264a7ff5d9e1010ec5d861539bc779bb1677a4a37872da'}}
		# a9a9b15083dd3bf249264a7ff5d9e1010ec5d861539bc779bb1677a4a37872da
		# e98095b5fed901f947f5c6683b82514fad519e7c96db065a52a60f92fbd4591f
		ext = json.dumps(showExt, separators=(',', ':'))
		self._url = API_URL.format(variables=var, extensions=ext)

	def crawl(self):
		cusHeaders = {
			'TE': 'Trailers',
			'Origin': 'https://www.ardmediathek.de',
			'content-type': 'application/json',
			'Accept': '*/*',
			'Referer': 'https://www.ardmediathek.de/ard/shows/Y3JpZDovL25kci5kZS8xMzkx/45-min',
			'User-Agent': 'monobear.business Crawler',
			'DNT': '1'
		}

		# first send OPTIONS
		stTime = time.perf_counter()
		respOptions = requests.options(self._url, headers=cusHeaders)
		etTime = time.perf_counter()
		logger.debug('OPTIONS film {:s}/{:s}/{:s}: {:.5f}'.format(self._sender, self._topic, self._title, etTime-stTime))

		stTime = time.perf_counter()
		r = None
		try:
			r = requests.get(self._url, headers=cusHeaders)
		except urllib.error.HTTPError:
			logger.error('Could not retrieve info for {:s} ({:s})'.format(self._title, self._showTitle))
		finally:
			etTime = time.perf_counter()
			logger.debug('crawl film {:s}/{:s}/{:s}: {:.5f}'.format(self._sender, self._topic, self._title, etTime-stTime))

		if not r or r.status_code != 200:
			raise Exception('Could not retrieve stream informations.')

		# now we need to extract some data.
		js = json.loads(r.text)
		for sa in js['data']['playerPage']['mediaCollection']['_mediaArray']:
			for media in sa['_mediaStreamArray']:
				for stream in media['_stream']:
					self._links.append({'_quality': media['_quality'], '_stream': stream})

		# some meta information?
		self._title = js['data']['playerPage']['title']
		self._duration = js['data']['playerPage']['tracking']['atiCustomVars']['clipLength']
		self._contentId = js['data']['playerPage']['tracking']['atiCustomVars']['contentId']
		self._channel = js['data']['playerPage']['tracking']['atiCustomVars']['channel']
		self._blockedByFsk = js['data']['playerPage']['blockedByFsk']
		self._geoBlocked = js['data']['playerPage']['geoblocked']
		self._broadcastOn = datetime.datetime.strptime(js['data']['playerPage']['broadcastedOn'], '%Y-%m-%dT%H:%M:%SZ')
		try:
			self._availableUntil = datetime.datetime.strptime(js['data']['playerPage']['availableTo'], '%Y-%m-%dT%H:%M:%SZ')
		except TypeError:
			self._availableUntil = None

class ArdShow(object):

	def __init__(self, id):
		self._id = id
		self._filmList = []
		self._sender = ''
		self._title = ''
		self._synopsis = ''
		showVars = {
			'client': 'ard',
			'showId': self._id
		}
		var = json.dumps(showVars, separators=(',', ':'))
		showExt = {'persistedQuery':{'version':1,'sha256Hash':'e98095b5fed901f947f5c6683b82514fad519e7c96db065a52a60f92fbd4591f'}}
		ext = json.dumps(showExt, separators=(',', ':'))
		self._url = API_URL.format(variables=var, extensions=ext)

		showExt = {'persistedQuery':{'version':1,'sha256Hash':'1f680c1618207fa89687afcdac128bd15f6923b5d1fef57fdd30aac716b9239e'}}
		ext = json.dumps(showExt, separators=(',', ':'))
		self._mediaUrl = API_URL.format(variables=var, extensions=ext)

	def crawl(self):
		cusHeaders = {
			'TE': 'Trailers',
			'Origin': 'https://www.ardmediathek.de',
			'content-type': 'application/json',
			'Accept': '*/*',
			'Referer': 'https://www.ardmediathek.de/ard/shows/Y3JpZDovL25kci5kZS8xMzkx/45-min',
			'User-Agent': 'monobear.business Crawler',
			'DNT': '1'
		}

		# first send OPTIONS
		stTime = time.perf_counter()
		respOptions = requests.options(self._url, headers=cusHeaders)
		etTime = time.perf_counter()
		logger.debug('OPTIONS show {:s}: {:.5f}'.format(self._id, etTime-stTime))

		stTime = time.perf_counter()
		r = None
		try:
			r = requests.get(self._url, headers=cusHeaders)
		except urllib.error.HTTPError:
			logger.error('Could not retrieve info for {:s}/{:s}'.format(self._sender, self._title))
		finally:
			etTime = time.perf_counter()
			logger.debug('crawl show {:s}: {:.5f}'.format(self._id, etTime-stTime))

		if not r or r.status_code != 200:
			raise Exception('Could not retrieve show details.')

		data = json.loads(r.text)
		self._title = data['data']['showPage']['title']
		self._synopsis = data['data']['showPage']['synopsis']
		self._sender = data['data']['showPage']['publicationService']['name']
		
		self.crawlMedia()

	def crawlMedia(self):
		cusHeaders = {
			'TE': 'Trailers',
			'Origin': 'https://www.ardmediathek.de',
			'content-type': 'application/json',
			'Accept': '*/*',
			'Referer': 'https://www.ardmediathek.de/ard/shows/Y3JpZDovL25kci5kZS8xMzkx/45-min',
			'User-Agent': 'monobear.business Crawler',
			'DNT': '1'
		}

		# first send OPTIONS
		stTime = time.perf_counter()
		respOptions = requests.options(self._mediaUrl, headers=cusHeaders)
		etTime = time.perf_counter()
		logger.debug('OPTIONS media {:s}/{:s}: {:.5f}'.format(self._sender, self._title, etTime-stTime))

		stTime = time.perf_counter()
		r = None
		try:
			r = requests.get(self._mediaUrl, headers=cusHeaders)
		except urllib.error.HTTPError:
			logger.error('Could not retrieve media for {:s}/{:s}'.format(self._sender, self._title))
		finally:
			etTime = time.perf_counter()
			logger.debug('crawl media {:s}/{:s}: {:.5f}'.format(self._sender, self._title, etTime-stTime))
		
		if not r or r.status_code != 200:
			raise Exception('Could not retrieve show details.')

		data = json.loads(r.text)
		for film in data['data']['showPage']['teasers']:
			f = ArdFilm(film['id'])
			f._sender = self._sender
			f._topic = self._title
			f._availableTo = film['availableTo']
			f._broadcastOn = film['broadcastedOn']
			f._duration = film['duration']
			f._title = film['longTitle']
			self._filmList.append(f)
			try:
				f.crawl()
			except Exception:
				self._filmList.remove(f)

class ArdParser(object):

	def __init__(self):
		crawlerVars = {
			'client': 'ard'
		}
		crawlerExtension = {
			'persistedQuery': {
				'version':1,
				'sha256Hash':'fdbab76da7d6aeb1ae859e1758dd1db068824dbf1623c02bc4c5f61facb474c2'
			}
		}
		ext = json.dumps(crawlerExtension, separators=(',', ':'))
		var = json.dumps(crawlerVars, separators=(',', ':'))
		self._url = API_URL.format(variables=var, extensions=ext)
		self._shows = []

	def crawl(self):
		cusHeaders = {
			'TE': 'Trailers',
			'Origin': 'https://www.ardmediathek.de',
			'content-type': 'application/json',
			'Accept': '*/*',
			'Referer': 'https://www.ardmediathek.de/ard/shows/Y3JpZDovL25kci5kZS8xMzkx/45-min',
			'User-Agent': 'monobear.business Crawler',
			'DNT': '1'
		}

		# first send OPTIONS
		stTime = time.perf_counter()
		respOptions = requests.options(self._url, headers=cusHeaders)
		etTime = time.perf_counter()
		logger.debug('OPTIONS parser: {:.5f}'.format(etTime-stTime))

		stTime = time.perf_counter()
		r = None
		try:
			r = requests.get(self._url, headers=cusHeaders)
		except urllib.error.HTTPError:
			logger.error('Could not retrieve parser info')
		finally:
			etTime = time.perf_counter()
			logger.debug('crawl parser: {:.5f}'.format(etTime-stTime))
		
		if not r or r.status_code != 200:
			raise Exception('Could not receive list of shows.')

		threads = []
		lsShow = json.loads(r.text)
		for alpha, teaserList in lsShow['data']['showsPage']['glossary'].items():
			if type(teaserList).__name__ == 'list':
				for teaser in teaserList:
					if teaser['__typename'] == 'Teaser':
						shw = ArdShow(teaser['id'])
						self._shows.append(shw)
						t = threading.Thread(target=shw.crawl)
						t.start()
						threads.append(t)

		del(r)
		for t in threads:
			t.join()

if __name__ == '__main__':
	ard = ArdParser()
	ard.crawl()
	# count shows, films, etc.
	noShows = 0
	noFilms = 0
	noLinks = 0

	for s in ard._shows:
		noShows += 1
		for f in s._filmList:
			noFilms += 1
			for l in f._links:
				noLinks += 1

	print('Found: {:d} links in {:d} films in {:d} shows.'.format(noLinks, noFilms, noShows))