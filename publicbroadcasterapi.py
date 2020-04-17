#!/usr/bin/env python3
import urllib.parse
import requests
import json
import sys
import shlex
import subprocess

PLAYER_ID = 'ngplayer_2_3'
PLAYER = 'mplayer'
PLAYER_HLS = 'ffplay'

class Zdf3SatApi(object):

	def __init__(self, endpoint, fallbackToken=None):
		self.endpoint = endpoint
		self.fallbackToken = fallbackToken

	@property
	def apiTokenUri(self):
		return self.endpoint['apiTokenUri']

	@property
	def apiUrl(self):
		return self.endpoint['apiUrl']

	@property
	def apiPath(self):
		return self.endpoint['apiPath']

	@property
	def apiParams(self):
		return self.endpoint['apiParams']

	def getBasePath(self, url):
		urlAnalyze = urllib.parse.urlparse(url)
		try:
			return urlAnalyze.path.rstrip('.html')
		except:
			raise Exception('Invalid URL given!')

	def getAPIToken(self, url):
		api = None
		r = requests.get(self.apiTokenUri)
		if r.status_code == 200:
			jc = r.json()
			api = '%s %s' % (jc['type'].capitalize(), jc['token'])

		if api is None:
			sys.stderr.write('Could not retrieve the API token!')
			return None
		else:
			self._tokenHeader = api
			return api

	def fetchStream(self, url):
		streams = {}
		streamFileName = self.getBasePath(url)
		if not self.fallbackToken:
			token = self.getAPIToken(url)
			if not token:
				raise Exception('No API token available.')
		else:
			token = self.fallbackToken(url)

		fullUrl = self.apiUrl + '/' + self.apiPath + '/' + streamFileName + '.json' + self.apiParams
		#print('Fetch URL: ', fullUrl)
		r = requests.get(fullUrl, headers={'Api-Auth': token})
		if r.status_code == 403:
			raise Exception('Permission denied! We\'re not allowed to request configuration file.')
		elif r.status_code != 200:
			raise Exception('Could not retrieve the configuration file!')

		config = r.json()
		if not 'hasVideo' in config.keys():
			raise Exception('Could not retrieve the configuration file (important info not given)!')
		if not config['hasVideo']:
			raise Exception('Site does not contain any video anymore!')
		try:
			nextUrlPath = config['mainVideoContent']['http://zdf.de/rels/target']['http://zdf.de/rels/streams/ptmd']
		except KeyError:
			nextUrlPath = config['mainVideoContent']['http://zdf.de/rels/target']['http://zdf.de/rels/streams/ptmd-template']
		finally:
			nextUrlPath = nextUrlPath.replace('{playerId}', PLAYER_ID)
		#print('Found next URL path: %s' % (nextUrlPath,))

		fullUrl = self.apiUrl + ('/' if nextUrlPath[:1] != '/' else '') + nextUrlPath
		#print('Fetch URL: ', fullUrl)
		r = requests.get(fullUrl, headers={'Api-Auth': token})
		if r.status_code != 200:
			raise Exception('Could not retrieve the stream information!')

		streamInfo = r.json()
		# now try to fetch.
		for e in streamInfo['priorityList']:
			for fl in e['formitaeten']:
				streams[fl['mimeType']] = {}
				# for mime type video/mp4, we might need to manipulate the streams!
				# steps: 808k (low), 1628k (med), 3328k (veryhigh)
				for qual in fl['qualities']:
					qualKey = 'XQ'
					if qual['hd'] == True:
						qualKey = 'HD'
					elif qual['quality'] == 'auto':
						qualKey = 'XQ'
					elif qual['quality'] == 'low':
						qualKey = 'MQ'
					elif qual['quality'] == 'med':
						qualKey = 'HQ'
					elif qual['quality'] == 'high':
						qualKey = 'EQ'
					elif qual['quality'] == 'veryhigh':
						qualKey = 'SQ'
					for track in qual['audio']['tracks']:
						# track['class'] contains information about type of stream:
						# ad = audio description
						# main = regular
						if track['class'] in ['ad']:
							continue
						# seems like the quality code for video/mp4 is a bit
						# wrong assigned by ZDF
						if fl['mimeType'] == 'video/mp4' and track['uri'].endswith('808k_p11v15.mp4'):
							qualKey = 'MQ'
						# do not override!
						if fl['mimeType'] == 'video/mp4' and qualKey == 'SQ':
							trackList = self.extractHQUrls(qualKey, track['uri'])
							for x in trackList:
								streams[fl['mimeType']][x[0]] = x[1]
						elif qualKey not in streams[fl['mimeType']].keys() or len(streams[fl['mimeType']][qualKey]) <= 0:
							streams[fl['mimeType']][qualKey] = track['uri']
		return streams

	def extractHQUrls(self, oQual, oUri):
		trackList = []
		added = []
		uriCombi = [
			('1456k_p13v12.mp4', '3328k_p36v12.mp4', 'HQ', 'EQ'),
			('2256k_p14v12.mp4', '3328k_p36v12.mp4', 'HQ', 'EQ'),
			('2328k_p35v12.mp4', '3328k_p36v12.mp4', 'HQ', 'EQ'),
			('1456k_p13v12.mp4', '3256k_p15v12.mp4', 'HQ', 'EQ'),
			('2256k_p14v12.mp4', '3256k_p15v12.mp4', 'HQ', 'EQ'),
			('2328k_p35v12.mp4', '3256k_p15v12.mp4', 'HQ', 'EQ'),
			('1496k_p13v13.mp4', '3296k_p15v13.mp4', 'HQ', 'EQ'),
			('2296k_p14v13.mp4', '3296k_p15v13.mp4', 'HQ', 'EQ'),
			('2328k_p35v13.mp4', '3296k_p15v13.mp4', 'HQ', 'EQ'),
			('1496k_p13v13.mp4', '3328k_p36v13.mp4', 'HQ', 'EQ'),
			('2296k_p14v13.mp4', '3328k_p36v13.mp4', 'HQ', 'EQ'),
			('2328k_p35v13.mp4', '3328k_p36v13.mp4', 'HQ', 'EQ'),
			('1496k_p13v14.mp4', '3328k_p36v14.mp4', 'HQ', 'EQ'),
			('2296k_p14v14.mp4', '3328k_p36v14.mp4', 'HQ', 'EQ'),
			('2328k_p35v14.mp4', '3328k_p36v14.mp4', 'HQ', 'EQ'),
			('1496k_p13v14.mp4', '3328k_p35v14.mp4', 'HQ', 'EQ'),
			('2296k_p14v14.mp4', '3328k_p35v14.mp4', 'HQ', 'EQ'),
			('2328k_p35v14.mp4', '3328k_p35v14.mp4', 'HQ', 'EQ'),
			('1628k_p13v15.mp4', '3360k_p36v15.mp4', 'HQ', 'SQ'),
			('2360k_p35v15.mp4', '3360k_p36v15.mp4', 'HQ', 'SQ'),
		]
		for x in uriCombi:
			if oUri.endswith(x[0]):
				if oUri not in added:
					trackList.append(
						(x[2], oUri)
					)
					added.append(oUri)
				newUri = oUri.replace(x[0], x[1])
				if newUri not in added:
					r = requests.head(newUri)
					if r.status_code == 200:
						trackList.append(
							(x[3], newUri)
						)
						added.append(newUri)
		return trackList

	def printStreams(self, streams, play=False):
		i = 0
		print('')
		streamNumbered = []
		streamInfo = []
		for streamType, qualStreams in streams.items():
			print(streamType + ':')
			print((len(streamType) + 1)*'=')

			for qualKey in ['XQ', 'MQ', 'HQ', 'EQ', 'SQ', 'HD']:
				if qualKey in qualStreams.keys():
					playNo = ''
					if play:
						playNo = '[{:>2d}] '.format(i)
						streamNumbered.append(qualStreams[qualKey])
						streamInfo.append(streamType)
						i += 1
					print('    ' + playNo + qualKey + ': ' + qualStreams[qualKey])
					print(' ')

		if play:
			playNo = input('> ')
			try:
				playNo = int(playNo.strip())
			except ValueError:
				sys.stderr.write('Invalid number given. Cancel.\n')
			else:
				try:
					streamUrl = streamNumbered[playNo]
				except KeyError:
					sys.stderr.write('Stream # not existant.\n')
				else:
					if streamInfo[playNo] == 'application/x-mpegURL':
						selectedPlayer = PLAYER_HLS
					else:
						selectedPlayer = PLAYER
					fullCmd = shlex.split(selectedPlayer + ' "' + streamUrl + '"')
					subprocess.Popen(fullCmd)

