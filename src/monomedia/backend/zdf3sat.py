#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8:ts=4:sw=4:sta:et:sts=4:fdm=marker:ai

from monomedia.api import MediaBackend
from monomedia.model import Playlist, PlaylistItem, PlaylistItemStream
import monomedia.player
import urllib.parse
import requests
import json
import sys
import logging

PLAYER_ID = 'ngplayer_2_3'

class Zdf3SatMediaBackend(MediaBackend):

    def __init__(self, endpoint, fallbackToken=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log = logging.getLogger(__name__)
        self.endpoint = endpoint
        self.fallbackToken = fallbackToken

    def getChannel(self):
        return '3Sat/ZDF'

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

    def play(self, mediaIndex = None):
        if self.live:
            mediaPlayer = monomedia.player.getPlayer()(self.getLiveStream())
        else:
            mediaPlayer = monomedia.player.getPlayer()(self.playlist.getStream(mediaIndex)[1])

        mediaPlayer.play()

    def load(self):
        if self.live:
            return True

        streamFileName = self.getBasePath(self.media)
        if not self.fallbackToken:
            token = self.getAPIToken(self.media)
            if not token:
                raise Exception('No API token available.')
        else:
            token = self.fallbackToken(self.media)

        fullUrl = self.apiUrl + '/' + self.apiPath + '/' + streamFileName + '.json' + self.apiParams
        self._log.debug('Fetch URL: {:s}'.format(fullUrl))
        r = requests.get(fullUrl, headers={'Api-Auth': token})
        if r.status_code == 403:
            raise Exception('Permission denied! We\'re not allowed to request configuration file.')
        elif r.status_code != 200:
            raise Exception('Could not retrieve the configuration file!')

        config = r.json()
        #print(config['title'])
        #print(config['subtitle'])
        #print(config['leadParagraph'])
        #print(config['teasertext'])
        #print(config['fskBlocked'])
        #print(config['endDate'])
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
        self._log.debug('Found next URL path: {:s}'.format(nextUrlPath))

        fullUrl = self.apiUrl + ('/' if nextUrlPath[:1] != '/' else '') + nextUrlPath
        self._log.debug('Fetch URL: {:s}'.format(fullUrl))
        r = requests.get(fullUrl, headers={'Api-Auth': token})
        if r.status_code != 200:
            raise Exception('Could not retrieve the stream information!')

        streamInfo = r.json()

        playlist = Playlist()
        duration = int(streamInfo['attributes']['duration']['value']/1000)
        item = PlaylistItem(config['title'], duration)
        item.channel = self.getChannel()
        item._description = config['leadParagraph']

        # now try to fetch.
        for e in streamInfo['priorityList']:
            for fl in e['formitaeten']:
                # for mime type video/mp4, we might need to manipulate the streams!
                # steps: 808k (low), 1628k (med), 3328k (veryhigh)
                for qual in fl['qualities']:
                    qualKey = PlaylistItemStream.QUALITY_AUTO
                    if qual['quality'] == 'auto':
                        qualKey = PlaylistItemStream.QUALITY_AUTO
                    elif qual['quality'] == 'low':
                        qualKey = PlaylistItemStream.QUALITY_LQ
                    elif qual['quality'] == 'med':
                        qualKey = PlaylistItemStream.QUALITY_HQ
                    elif qual['quality'] == 'high':
                        qualKey = PlaylistItemStream.QUALITY_EQ
                    elif qual['quality'] == 'veryhigh':
                        qualKey = PlaylistItemStream.QUALITY_SQ
                    elif qual['hd'] == True:
                        qualKey = PlaylistItemStream.QUALITY_HD
                    for track in qual['audio']['tracks']:
                        # track['class'] contains information about type of stream:
                        # ad = audio description
                        # main = regular
                        if track['class'] in ['ad']:
                            continue
                        # seems like the quality code for video/mp4 is a bit
                        # wrong assigned by ZDF
                        if fl['mimeType'] == 'video/mp4' and track['uri'].endswith('808k_p11v15.mp4'):
                            qualKey = PlaylistItemStream.QUALITY_HQ
                        # do not override!
                        if fl['mimeType'] == 'video/mp4' and qualKey == PlaylistItemStream.QUALITY_SQ:
                            trackList = self.extractHQUrls(qualKey, track['uri'])
                            for x in trackList:
                                stream = PlaylistItemStream(
                                    x[0], x[1]
                                )
                                item.append(stream)
                        else:
                            stream = PlaylistItemStream(
                                qualKey, track['uri']
                            )
                            item.append(stream)
        playlist.append(item)

        if playlist:
            self.setPlaylist(playlist)
            return True
        else:
            self._log.error('Could not find any stream!')
            return False

    def extractHQUrls(self, oQual, oUri):
        trackList = []
        added = []
        uriCombi = [
            ('1456k_p13v12.mp4', '3328k_p36v12.mp4', 'HQ', 'HD'),
            ('2256k_p14v12.mp4', '3328k_p36v12.mp4', 'EQ', 'HD'),
            ('2328k_p35v12.mp4', '3328k_p36v12.mp4', 'EQ', 'HD'),
            ('1456k_p13v12.mp4', '3256k_p15v12.mp4', 'HQ', 'HD'),
            ('2256k_p14v12.mp4', '3256k_p15v12.mp4', 'EQ', 'HD'),
            ('2328k_p35v12.mp4', '3256k_p15v12.mp4', 'EQ', 'HD'),
            ('1496k_p13v13.mp4', '3296k_p15v13.mp4', 'HQ', 'HD'),
            ('2296k_p14v13.mp4', '3296k_p15v13.mp4', 'EQ', 'HD'),
            ('2328k_p35v13.mp4', '3296k_p15v13.mp4', 'EQ', 'HD'),
            ('1496k_p13v13.mp4', '3328k_p36v13.mp4', 'HQ', 'SQ'),
            ('2296k_p14v13.mp4', '3328k_p36v13.mp4', 'EQ', 'SQ'),
            ('2328k_p35v13.mp4', '3328k_p36v13.mp4', 'EQ', 'SQ'),
            ('1496k_p13v14.mp4', '3328k_p36v14.mp4', 'HQ', 'SQ'),
            ('2296k_p14v14.mp4', '3328k_p36v14.mp4', 'EQ', 'SQ'),
            ('2328k_p35v14.mp4', '3328k_p36v14.mp4', 'EQ', 'SQ'),
            ('1496k_p13v14.mp4', '3328k_p35v14.mp4', 'HQ', 'SQ'),
            ('2296k_p14v14.mp4', '3328k_p35v14.mp4', 'EQ', 'SQ'),
            ('2328k_p35v14.mp4', '3328k_p35v14.mp4', 'EQ', 'SQ'),
            ('1628k_p13v15.mp4', '3360k_p36v15.mp4', 'HQ', 'XQ'),
            ('2360k_p35v15.mp4', '3360k_p36v15.mp4', 'EQ', 'XQ'),
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
            try:
                if item._broadcastOn:
                    print(
                        'Media is casted on {broadcast}.'.format(
                            broadcast=item._broadcastOn.strftime('%d.%m.%Y %H:%M:%S%z')
                        )
                    )
            except AttributeError:
                pass

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

class ZDFMediaBackend(Zdf3SatMediaBackend):
    ENDPOINT = {
        'apiTokenUri': 'https://zdf-cdn.live.cellular.de/mediathekV2/token',
        'apiUrl': 'https://api.zdf.de',
        'apiPath': 'content/documents/zdf',
        'apiParams': '?profile=player'
    }

    def __init__(self, *args, **kwargs):
        super().__init__(self.ENDPOINT, None, *args, **kwargs)

    def getChannel(self):
        return 'ZDF'

    @staticmethod
    def isResponsible(url, live=False):
        if 'zdf.de' in url:
            return True
        elif live and url.lower() in ['zdf',]:
            return True
        else:
            return False

    def hasSelection(self):
        return not self.live

    def getLiveStream(self):
        return PlaylistItemStream('auto', 'https://zdf-hls-15.akamaized.net/hls/live/2016498/de/high/master.m3u8')

class DreiSatMediaBackend(Zdf3SatMediaBackend):
    ENDPOINT = {
        'apiTokenUri': 'https://zdf-cdn.live.cellular.de/mediathekV2/token',
        'apiUrl': 'https://api.3sat.de',
        'apiPath': 'content/documents/zdf',
        'apiParams': '?profile=player'
    }
    API_TOKEN_PREFIX = 'Bearer'

    def __init__(self, *args, **kwargs):
        super().__init__(self.ENDPOINT, self.token3Sat, *args, **kwargs)

    def getChannel(self):
        return '3sat'

    def token3Sat(self, url):
        api = None
        self._log.debug('Fetch URL: {:s}'.format(url))
        r = requests.get(url)
        if r.status_code == 200:
            cnt = r.text
            startPosition = cnt.find('data-zdfplayer-jsb')
            if startPosition > -1:
                    endPosition = cnt.find('}', cnt.find('data-zdfplayer-jsb'))
                    if endPosition > -1:
                            jc = cnt[startPosition+20:endPosition+1]
                            try:
                                    jc = json.loads(jc.replace('\n', ''))
                                    api = '%s %s' % (self.API_TOKEN_PREFIX, jc['apiToken'])
                            except:
                                    pass

        if api is None:
            self._log.error('Could not retrieve the API token!')
        else:
            self._log.debug('Found API-Token: {:s}'.format(api))
            return api

    @staticmethod
    def isResponsible(url, live=False):
        if '3sat.de' in url:
            return True
        elif live and url.lower() in ['3sat',]:
            return True
        else:
            return False

    def hasSelection(self):
        return not self.live

    def getLiveStream(self):
        return PlaylistItemStream('auto', 'https://zdf-hls-18.akamaized.net/hls/live/2016501/dach/high/master.m3u8')

