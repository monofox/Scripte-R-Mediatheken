#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8:ts=4:sw=4:sta:et:sts=4:fdm=marker:ai

from monomedia.api import MediaBackend
from monomedia.model import Playlist, PlaylistItem, PlaylistItemStream
import monomedia.player
import requests
import sys
import shlex
import subprocess
import urllib.parse
import os.path
import datetime
import logging
import logging.handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger()
log.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
log.addHandler(ch)

PLAYER_ID = 'ngplayer_2_3'
CONFIG_PATTERN = 'https://page.ardmediathek.de/page-gateway/pages/daserste/item/{mediaId}?devicetype=pc'

class ArdMediaHolder(PlaylistItem):

    def __init__(self, title, channel, *args, **kwargs):
        super().__init__(title=title, *args, **kwargs)

        self._holder = []
        self._js = {}

        # metadata information
        self.channel = channel
        self._contentId = 0
        self._clipLength = 0

        self._geoBlocked = None
        self._blockedByFsk = None
        self._broadcastOn = None
        self._availableUntil = None

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

class ARDMediaBackend(MediaBackend):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def isResponsible(url, live=False):
        if 'ardmediathek.de' in url:
            return True
        elif live and url.lower() in ['ard', 'daserste']:
            return True
        else:
            return False

    def hasSelection(self):
        return not self.live

    def getLiveStream(self):
        return PlaylistItemStream('auto', 'https://mcdn.daserste.de/daserste/de/master.m3u8')

    def play(self, mediaIndex = None):
        if self.live:
            mediaPlayer = monomedia.player.getPlayer()(self.getLiveStream())
        else:
            mediaPlayer = monomedia.player.getPlayer()(self.playlist.getStream(mediaIndex))

        mediaPlayer.play()

    def getMediaId(self):
        docpath = urllib.parse.urlsplit(self.media).path
        if docpath.endswith('/'):
            docpath = docpath[:-1]

        return os.path.split(docpath)[-1]

    def load(self):
        if self.live:
            return True

        mediaId = self.getMediaId()
        mediaUrl = CONFIG_PATTERN.format(mediaId=mediaId)

        req = requests.get(mediaUrl)
        if req.status_code != 200:
            log.error('Could not retrieve corresponding video page!')
            return False

        data = req.json()
        playlist = Playlist()
        item = ArdMediaHolder(data['title'], data['tracking']['atiCustomVars']['channel'])
        # meta information
        item._contentId = data['tracking']['atiCustomVars']['contentId']
        item._clipLength = data['tracking']['atiCustomVars']['clipLength']
        # media information
        item._geoBlocked = data['widgets'][0]['geoblocked']
        item._blockedByFsk = data['widgets'][0]['blockedByFsk']
        item._broadcastOn = datetime.datetime.strptime(data['widgets'][0]['broadcastedOn'], '%Y-%m-%dT%H:%M:%SZ')
        if data['widgets'][0]['availableTo']:
            item._availableUntil = datetime.datetime.strptime(data['widgets'][0]['availableTo'], '%Y-%m-%dT%H:%M:%SZ')

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
                        item.append(PlaylistItemStream(self._convertQuality(media['_quality']), streamDecoded))
                else:
                    try:
                        streamDecoded = urllib.parse.unquote(media['_stream'])
                    except:
                        streamDecoded = media['_stream']
                    item.append(PlaylistItemStream(self._convertQuality(media['_quality']), streamDecoded))

        playlist.append(item)

        if playlist:
            self.setPlaylist(playlist)
            return True
        else:
            log.error('Could not find any stream!')
            return False

    def _convertQuality(self, quality):
        qualKey = quality
        if quality == 0:
            qualKey = PlaylistItemStream.QUALITY_LQ
        elif quality == 1:
            qualKey = PlaylistItemStream.QUALITY_MQ
        elif quality == 2:
            qualKey = PlaylistItemStream.QUALITY_HQ
        elif quality == 3:
            qualKey = PlaylistItemStream.QUALITY_HD
        elif quality == 4:
            qualKey = PlaylistItemStream.QUALITY_SQ
        elif quality == 'auto':
            qualKey = PlaylistItemStream.QUALITY_AUTO
        return qualKey

    def printSelection(self):
        """
        Prints all found streams (streams consist of ArdMediaHolder)
        """
        # print some metadata
        for item in self.playlist:
            titleMsg = '{channel}: {title} ({clipLength})'.format(
                    channel=item.channel,
                    title=item.title,
                    clipLength=item.format_duration()
                )
            print(titleMsg)
            print('-'*len(titleMsg))

            # we need to resort the qualStreams.
            lastQuality = None
            i = 0
            for metaStream in item:
                if not lastQuality or lastQuality != metaStream.quality:
                    print('')
                    print(metaStream.quality + ':')
                    lastQuality = metaStream.quality
                    
                playNo = ''
                streamList = []
                streamList.append(metaStream.stream)

                for streamEntry in streamList:
                    if streamEntry.startswith('//'):
                        streamEntry = 'https:' + streamEntry
                    playNo = '[{:>2d}] '.format(i)
                    i += 1
                    print('    ' + playNo + ': ' + streamEntry)
            print(' ')

            # some more information available?
            if item._blockedByFsk:
                print('This media is restricted by FSK!')
            
            if item._broadcastOn and item._availableUntil:
                print(
                    'Media is casted on {broadcast}Z and available until {available}Z'.format(
                        broadcast=item._broadcastOn.strftime('%d.%m.%Y %H:%M:%S'),
                        available=item._availableUntil.strftime('%d.%m.%Y %H:%M:%S')
                    )
                )
            elif item._broadcastOn:
                print(
                    'Media is casted on {broadcast}Z.'.format(
                        broadcast=item._broadcastOn.strftime('%d.%m.%Y %H:%M:%S')
                    )
                )
            elif item._availableUntil:
                print(
                    'Media is available until {available}Z.'.format(
                        available=item._availableUntil.strftime('%d.%m.%Y %H:%M:%S')
                    )
                )

        print(' ')

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
                    stream = self.playlist.getStream(playNo)
                    if not stream:
                        sys.stderr.write('Stream # does not exist.\n')
                    else:
                        return playNo
        return None
