#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8:ts=4:sw=4:sta:et:sts=4:fdm=marker:ai

from monomedia.api import MediaBackend
from monomedia.model import Playlist, PlaylistItem, PlaylistItemStream
import monomedia.player
import requests
import sys
from lxml import etree
from xml.dom import minidom
import datetime
import xmltodict
import logging

class ArteMediaBackend(MediaBackend):
    API_URL = 'https://api.arte.tv'
    API_PATH = 'api/player/v1/config/de'
    API_PARAMS = '?autostart=0&lifeCycle=1'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log = logging.getLogger(__name__)

    def getMovieID(self) -> str:
        # for certain urls (especially concert.arte.tv), it is necessary to retrieve
        # the real website first. 
        fullUrl = None
        extrUrl = None
        if self.media.endswith('/'):
            url = self.media[:-1]
        else:
            url = self.media
        try:
            extrUrl = url.split('/')[-2:-1][0]
        except:
            raise Exception('Invalid URL given!')

        # now whats the result?
        try:
            moveId = int(extrUrl[:2])
        except ValueError:
            extrUrl = None
            # OK.. no real move ID retrieved (starts always with number...)
            req = requests.get(self.media)
            if req.status_code != 200:
                raise Exception('Could not retrieve the original site!')

            cnt = req.text
            print(cnt)
            startPosition = cnt.find('arte_vp_url')
            if startPosition > -1:
                endPosition = cnt.find('"', startPosition + 14)
                if endPosition > -1:
                    fullUrl = cnt[startPosition+13:endPosition]
        else:
            fullUrl = self.API_URL + '/' + self.API_PATH + '/' + extrUrl + self.API_PARAMS

        if fullUrl is None:
            raise Exception('Could not find the API url!')
        return fullUrl

    @staticmethod
    def isResponsible(url, live=False):
        if 'arte.tv' in url:
            return True
        elif live and url.lower() in ['arte',]:
            return True
        else:
            return False

    def hasSelection(self):
        return not self.live

    def getLiveStream(self):
        # support to load from https://www.kika.de/videos/livestream/msl4/hls-livestream-100.xml ?
        return PlaylistItemStream('auto', 'https://artelive-lh.akamaihd.net/i/artelive_de@393591/master.m3u8')

    def play(self, mediaIndex = None):
        if self.live:
            mediaPlayer = monomedia.player.getPlayer()(self.getLiveStream())
        else:
            mediaPlayer = monomedia.player.getPlayer()(self.playlist.getStream(mediaIndex)[1])

        mediaPlayer.play()

    def load(self):
        if self.live:
            return True

        fullUrl = self.getMovieID()
        self._log.debug('Fetch URL: {:s}'.format(fullUrl))

        req = requests.get(fullUrl)
        if req.status_code != 200:
            raise Exception('Could not retrieve the configuration file!')

        streamInfo = req.json()
        
        playlist = Playlist(
            streamInfo['videoJsonPlayer']['VTI'],
            streamInfo['videoJsonPlayer']['videoDurationSeconds']
        )
        playlist.channel = streamInfo['videoJsonPlayer']['VTX']

        lastStreamKey = None
        xinfos = list(streamInfo['videoJsonPlayer']['VSR'].values())
        xinfos.sort(key=lambda x: x['versionCode'])
        for fle in xinfos:
            streamKey = '{:s}: {:s}'.format(
                fle['versionCode'], fle['versionLibelle']
            )
            if lastStreamKey != streamKey:
                if lastStreamKey:
                    playlist.append(item)
                lastStreamKey = streamKey
                item = PlaylistItem(
                    streamKey,
                    streamInfo['videoJsonPlayer']['videoDurationSeconds']
                )
                item._description = streamInfo['videoJsonPlayer']['VDE']
                item._broadcastOn = datetime.datetime.strptime(
                    streamInfo['videoJsonPlayer']['VRA'],
                    '%d/%m/%Y %H:%M:%S %z'
                )
                item._availableUntil = datetime.datetime.strptime(
                    streamInfo['videoJsonPlayer']['VRU'],
                    '%d/%m/%Y %H:%M:%S %z'
                )

            quality = self._convertQuality(fle['quality'])
            stream = PlaylistItemStream(
                quality,
                fle['url']
            )
            
            item.append(stream)
        
        playlist.append(item)

        if playlist:
            self.setPlaylist(playlist)
            return True
        else:
            self._log.error('Could not find any stream!')
            return False

    def _convertQuality(self, quality):
        if quality == 'XQ':
            quality = 'LQ'
        
        return quality

    def printSelection(self, selectDetail=False):
        """
        Prints all found streams (streams consist of ArdMediaHolder)
        """
        # print some metadata
        titleMsg = '{channel}: {title} ({clipLength})'.format(
            channel=self.playlist.channel,
            title=self.playlist.title,
            clipLength=self.playlist.duration
        )
        print(titleMsg)
        print('='*len(titleMsg))
        print('')


        i = 0
        for item in self.playlist:
            titleMsg = '{title} ({clipLength})'.format(
                title=item.title,
                clipLength=item.duration
            )
            print(titleMsg)
            print('-'*len(titleMsg))

            # we need to resort the qualStreams.
            lastQuality = None
            for metaStream in item:
                if not selectDetail and not metaStream.isBest:
                    continue
                if not lastQuality or lastQuality != metaStream.quality:
                    print('')
                    print(metaStream.quality + ':')
                    lastQuality = metaStream.quality
                    
                playNo = '[{:>2d}] '.format(i)
                i += 1
                print('    ' + playNo + ': ' + metaStream.stream)
            print(' ')

            # some more information available?
            if item._broadcastOn:
                print(
                    'Media is casted on {broadcast}.'.format(
                        broadcast=item._broadcastOn.strftime('%d.%m.%Y %H:%M:%S%z')
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
                    playNo, stream = self.playlist.getStream(playNo, not selectDetail)
                    if not stream:
                        sys.stderr.write('Stream # does not exist.\n')
                    else:
                        return playNo
        return None
