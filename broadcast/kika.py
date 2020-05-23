#!/usr/bin/env python3
import requests
import sys
import shlex
import subprocess
from lxml import etree
from xml.dom import minidom
import xmltodict

PLAYER_ID = 'ngplayer_2_3'
PLAYER = 'mplayer'
PLAYER_HLS = 'ffplay'

class KikaApi(object):

	def fetchStream(self, url):
		req = requests.get(url)
		if req.status_code != 200:
			raise Exception('Could not retrieve corresponding video page!')

		parser = etree.XMLParser(recover=True)
		root = etree.fromstring(req.text, parser)
		dom = minidom.parseString(etree.tostring(root))
		videoContainerDiv = None
		for element in dom.getElementsByTagName('div'):
			if element.hasAttribute('class'):
				classNames = element.getAttribute('class').split(' ')
				if 'av-playerContainer' in classNames:
					videoContainerDiv = element
					break
		if not videoContainerDiv:
			raise Exception('Cannot find video container!')

		videoConfigObject = None
		for child in videoContainerDiv.childNodes:
			if child.nodeName == 'a' and child.hasAttribute('onclick'):
				videoConfigObject = child.getAttribute('onclick')
				break

		if not videoConfigObject:
			raise Exception('Video config object couldn\'t be found.')

		urlStart = videoConfigObject.index('dataURL:')
		urlEnd = videoConfigObject.find('.xml', urlStart)
		videoConfigUrl = videoConfigObject[urlStart+9:urlEnd+4]
		if not videoConfigUrl:
			raise Exception('Couldn\'t extract config URL')

		req = requests.get(videoConfigUrl)
		if req.status_code != 200:
			raise Exception('Config URL found, but does not exist!')

		streams = {}
		doc = xmltodict.parse(req.text)
		for x, y in doc['avDocument']['assets'].items():
			for asset in y:
				profileName = asset['profileName']
				try:
					bitrate = int(asset['bitrateVideo'])
				except TypeError:
					bitrate = None
				try:
					frameWidth = int(asset['frameWidth'])
				except TypeError:
					frameWidth = None
				try:
					frameHeight = int(asset['frameHeight'])
				except TypeError:
					frameHeight = None
				if not bitrate:
					# sometimes, KiKA is strange..
					# figure out the bitrates, etc. just by profile names... :(
					videoURL = asset['progressiveDownloadUrl']
					if videoURL.endswith('476k_p9v14.mp4'):
						quality = 'MQ'
					elif videoURL.endswith('776k_p11v14.mp4'):
						quality = 'EQ'
					elif videoURL.endswith('1496k_p13v14.mp4'):
						quality = 'SQ'
					else:
						quality = 'NQ'
				elif bitrate >= 3300000:
					quality = 'SQ'
				elif bitrate >= 1800000:
					quality = 'EQ'
				elif bitrate >= 1500000:
					quality = 'HQ'
				elif bitrate >= 1000000:
					quality = 'MQ'
				elif bitrate >= 500000:
					quality = 'LQ'
				elif bitrate >= 250000:
					quality = 'XQ'
				else:
					quality = 'NQ'
				
				# check if application/x-mpegURL exist.
				mediaMapping = [
					('adaptiveHttpStreamingRedirectorUrl', 'application/x-mpegURL'),
					('progressiveDownloadUrl', 'video/mp4'),
					('dynamicHttpStreamingRedirectorUrl', 'application/f4m+xml'),
				]
				for mediaType in mediaMapping:
					if mediaType[0] in asset.keys():
						if asset[mediaType[0]]:
							if mediaType[1] not in streams.keys():
								streams[mediaType[1]] = {}
							streams[mediaType[1]][quality] = asset[mediaType[0]]

		return streams

	def printStreams(self, streams, play=False):
		i = 0
		print('')
		streamNumbered = []
		streamInfo = []
		for streamType, qualStreams in streams.items():
			print(streamType + ':')
			print((len(streamType) + 1)*'=')

			for qualKey in ['NQ', 'XQ', 'LQ', 'MQ', 'HQ', 'EQ', 'SQ']:
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

