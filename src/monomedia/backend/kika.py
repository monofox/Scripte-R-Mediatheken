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

class KikaMediaBackend(MediaBackend):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log = logging.getLogger(__name__)

    @staticmethod
    def isResponsible(url, live=False):
        if 'kika.de' in url:
            return True
        elif live and url.lower() in ['kika',]:
            return True
        else:
            return False

    def hasSelection(self):
        return not self.live

    def getLiveStream(self):
        # support to load from https://www.kika.de/videos/livestream/msl4/hls-livestream-100.xml ?
        return PlaylistItemStream('auto', 'https://kikageohls.akamaized.net/hls/live/2022693/livetvkika_de/master.m3u8')

    def play(self, mediaIndex = None):
        if self.live:
            mediaPlayer = monomedia.player.getPlayer()(self.getLiveStream())
        else:
            mediaPlayer = monomedia.player.getPlayer()(self.playlist.getStream(mediaIndex)[1])

        mediaPlayer.play()

    def load(self):
        if self.live:
            return True

        req = requests.get(self.media)
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

        doc = xmltodict.parse(req.text)
        playlist = Playlist()
        duration = 0
        factor = [1, 60, 60]
        durations = doc['avDocument']['duration'].split(':')
        durations.reverse()
        for x in durations:
            duration += int(x) * factor.pop(0)

        item = PlaylistItem(
            doc['avDocument']['title'],
            int(duration)
        )
        item.channel = "KIKA"
        item._publishedOn = datetime.datetime.strptime(
            doc['avDocument']['webTime'],
            '%d.%m.%Y %H:%M'
        )
        item._description = doc['avDocument']['broadcast']['broadcastDescription']
        item._broadcastOn = datetime.datetime.strptime(
            doc['avDocument']['broadcast']['broadcastDate'],
            '%Y-%m-%dT%H:%M:%S.%f%z'
        )

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
                        quality = PlaylistItemStream.QUALITY_MQ
                    elif videoURL.endswith('776k_p11v14.mp4'):
                        quality = PlaylistItemStream.QUALITY_EQ
                    elif videoURL.endswith('1496k_p13v14.mp4'):
                        quality = PlaylistItemStream.QUALITY_SQ
                    else:
                        quality = PlaylistItemStream.QUALITY_AUTO
                elif bitrate >= 3300000:
                    quality = PlaylistItemStream.QUALITY_XQ
                elif bitrate >= 1800000:
                    quality = PlaylistItemStream.QUALITY_SQ
                elif bitrate >= 1500000:
                    quality = PlaylistItemStream.QUALITY_HD
                elif bitrate >= 1000000:
                    quality = PlaylistItemStream.QUALITY_HQ
                elif bitrate >= 500000:
                    quality = PlaylistItemStream.QUALITY_MQ
                elif bitrate >= 250000:
                    quality = PlaylistItemStream.QUALITY_LQ
                else:
                    quality = PlaylistItemStream.QUALITY_AUTO
                
                # check if application/x-mpegURL exist.
                mediaMapping = [
                    ('adaptiveHttpStreamingRedirectorUrl', 'application/x-mpegURL'),
                    ('progressiveDownloadUrl', 'video/mp4'),
                    ('dynamicHttpStreamingRedirectorUrl', 'application/f4m+xml'),
                ]
                for mediaType in mediaMapping:
                    if mediaType[0] in asset.keys():
                        print(quality, mediaType[0])
                        if mediaType[0].startswith('adaptiveHttpStream'):
                            tempQuality = 'auto'
                        else:
                            tempQuality = quality
                        streamItem = PlaylistItemStream(
                            tempQuality,
                            asset[mediaType[0]]
                        )
                        item.append(streamItem)

        playlist.append(item)

        if playlist:
            self.setPlaylist(playlist)
            return True
        else:
            self._log.error('Could not find any stream!')
            return False

    def printSelection(self, selectDetail=False):
        """
        Prints all found streams (streams consist of ArdMediaHolder)
        """
        # print some metadata
        for item in self.playlist:
            titleMsg = '{channel}: {title} ({clipLength})'.format(
                channel=item.channel,
                title=item.title,
                clipLength=item.duration
            )
            print(titleMsg)
            print('-'*len(titleMsg))

            # we need to resort the qualStreams.
            lastQuality = None
            i = 0
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
