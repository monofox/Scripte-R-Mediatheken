#!/usr/bin/env python3
import requests
import sys
import shlex
import subprocess
import urllib.parse
import os.path
import datetime

PLAYER_ID = 'ngplayer_2_3'
PLAYER = 'mpv'
PLAYER_HLS = 'ffplay'
CONFIG_PATTERN = 'https://page.ardmediathek.de/page-gateway/pages/daserste/item/{mediaId}?devicetype=pc'

class ArdMediaHolder(object):

	def __init__(self):
		self._holder = []
		self._js = {}

		# metadata information
		self._title = ''
		self._channel = ''
		self._contentId = 0
		self._clipLength = 0

		self._geoBlocked = None
		self._blockedByFsk = None
		self._broadcastOn = None
		self._availableUntil = None

	def append(self, quality, uri):
		self._holder.append({
			'_quality': str(quality),
			'_stream': uri
		})

	def format_duration(self):
		"""
		Stole from: http://www.voidcn.com/article/p-qlzvdfdd-c.html
		"""
		seconds = self._clipLength
		if seconds == 0: return "now"
		origin = seconds
		dic = {
				'year': 60 * 60 * 24 * 365,
				'day': 60 * 60 * 24,
				'hour': 60 * 60,
				'minute': 60,
				'second': 1
		}
		spent = {}
		ans = ""
		for x in ['year','day','hour','minute','second']:
				spent[x] = seconds // dic[x]
				ans += "{}{} {}{}".format('' if seconds == origin else ' and ' if seconds % dic[x] == 0 else ', ',spent[x],x,'s' if spent[x] > 1 else '') if spent[x] > 0 else ''
				seconds %= dic[x]
		return ans

class ArdApi(object):

	def extractMediaId(self, url):
		docpath = urllib.parse.urlsplit(url).path
		if docpath.endswith('/'):
			docpath = docpath[:-1]

		return os.path.split(docpath)[-1]

	def fetchStream(self, url):
		mediaId = self.extractMediaId(url)
		mediaUrl = CONFIG_PATTERN.format(mediaId=mediaId)

		req = requests.get(mediaUrl)
		if req.status_code != 200:
			raise Exception('Could not retrieve corresponding video page!')

		data = req.json()
		holder = ArdMediaHolder()
		# meta information
		holder._title = data['title']
		holder._channel = data['tracking']['atiCustomVars']['channel']
		holder._contentId = data['tracking']['atiCustomVars']['contentId']
		holder._clipLength = data['tracking']['atiCustomVars']['clipLength']
		# media information
		holder._geoBlocked = data['widgets'][0]['geoblocked']
		holder._blockedByFsk = data['widgets'][0]['blockedByFsk']
		holder._broadcastOn = datetime.datetime.strptime(data['widgets'][0]['broadcastedOn'], '%Y-%m-%dT%H:%M:%SZ')
		if data['widgets'][0]['availableTo']:
			holder._availableUntil = datetime.datetime.strptime(data['widgets'][0]['availableTo'], '%Y-%m-%dT%H:%M:%SZ')

		# parse media streams
		streamDecoded = None
		for sa in data['widgets'][0]['mediaCollection']['embedded']['_mediaArray']:
			for media in sa['_mediaStreamArray']:
				if type(media['_stream']) == list:
					for stream in media['_stream']:
						# try to decode first!
						try:
							streamDecoded = urllib.parse.unquote(stream)
						except:
							streamDecoded = stream
						holder.append(media['_quality'], streamDecoded)
				else:
					try:
						streamDecoded = urllib.parse.unquote(media['_stream'])
					except:
						streamDecoded = media['_stream']
					holder.append(media['_quality'], streamDecoded)

		if holder._holder:
			return holder
		else:
			raise Exception('Could not found any stream!')

	def printStreams(self, streams, play=False):
		"""
		Prints all found streams (streams consist of ArdMediaHolder)
		"""
		# do we have some kind of meta information?
		if streams._title:
			titleMsg = '{channel}: {title} ({clipLength})'.format(
					channel=streams._channel,
					title=streams._title,
					clipLength=streams.format_duration()
				)
			print(titleMsg)
			print('-'*len(titleMsg) + '\n')

		i = 0
		streamNumbered = []
		availableQualities = []
		# get title of that language.
		for metaStream in streams._holder:
			qualKey = 'MQ'
			if metaStream['_quality'] == '0':
				qualKey = 'LQ'
			elif metaStream['_quality'] == '1':
				qualKey = 'MQ'
			elif metaStream['_quality'] == '2':
				qualKey = 'HQ'
			elif metaStream['_quality'] == '3':
				qualKey = 'EQ'
			elif metaStream['_quality'] == '4':
				qualKey = 'SQ'
			elif metaStream['_quality'] == 'auto':
				qualKey = 'auto'
			if qualKey not in availableQualities:
				availableQualities.append(qualKey)

		knownQuals = []
		for qual in ['auto', 'XQ', 'LQ', 'MQ', 'HQ', 'EQ', 'SQ']:
			if qual in availableQualities:
				knownQuals.append(qual)
		# we need to resort the qualStreams.
		for quality in knownQuals:
			print(quality + ':')
			for metaStream in streams._holder:
				qualKey = 'MQ'
				if metaStream['_quality'] == '0':
					qualKey = 'LQ'
				elif metaStream['_quality'] == '1':
					qualKey = 'MQ'
				elif metaStream['_quality'] == '2':
					qualKey = 'HQ'
				elif metaStream['_quality'] == '3':
					qualKey = 'EQ'
				elif metaStream['_quality'] == '4':
					qualKey = 'SQ'
				elif metaStream['_quality'] == 'auto':
					qualKey = 'auto'
				if qualKey == quality: 
					playNo = ''
					streamList = []
					streamList.append(metaStream['_stream'])

					for streamEntry in streamList:
						if streamEntry.startswith('//'):
							streamEntry = 'https:' + streamEntry
						if play:
							playNo = '[{:>2d}] '.format(i)
							streamNumbered.append(streamEntry)
							i += 1
						print('    ' + playNo + ': ' + streamEntry)
			print(' ')

		# some more information available?
		if streams._blockedByFsk:
			print('This media is restricted by FSK!')
		
		if streams._broadcastOn and streams._availableUntil:
			print(
				'Media is casted on {broadcast}Z and available until {available}Z'.format(
					broadcast=streams._broadcastOn.strftime('%d.%m.%Y %H:%M:%S'),
					available=streams._availableUntil.strftime('%d.%m.%Y %H:%M:%S')
				)
			)
		elif streams._broadcastOn:
			print(
				'Media is casted on {broadcast}Z.'.format(
					broadcast=streams._broadcastOn.strftime('%d.%m.%Y %H:%M:%S')
				)
			)
		elif streams._availableUntil:
			print(
				'Media is available until {available}Z.'.format(
					available=streams._availableUntil.strftime('%d.%m.%Y %H:%M:%S')
				)
			)

		print(' ')

		if play:
			playNo = input('> ')
			if playNo.strip().lower() == 'q':
				print('Bye, bye!')
			else:
				try:
					playNo = int(playNo.strip())
				except ValueError:
					sys.stderr.write('Invalid number given. Cancel.\n')
				else:
					if playNo < 0:
						sys.stderr.write('Invalid number given. Cancel.\n')
					else:
						try:
							streamUrl = streamNumbered[playNo]
						except KeyError:
							sys.stderr.write('Stream # not existant.\n')
						except IndexError:
							sys.stderr.write('Stream # not existant.\n')
						else:
							if streamUrl.endswith('.m3u8'):
								selectedPlayer = PLAYER_HLS
							else:
								selectedPlayer = PLAYER
							fullCmd = shlex.split(selectedPlayer + ' "' + streamUrl + '"')
							subprocess.Popen(fullCmd)
