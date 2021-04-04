#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8:ts=4:sw=4:sta:et:sts=4:fdm=marker:ai

from monomedia.api import MediaBackend
from monomedia.model import PlaylistItemStream
import monomedia.player
import sys
import logging

class Swr2MediaBackend(MediaBackend):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log = logging.getLogger(__name__)

    @staticmethod
    def isResponsible(url, live=False):
        if live and url.lower() == 'swr2':
            return True
        else:
            return False

    def hasSelection(self):
        return False

    def getLiveStream(self):
        return PlaylistItemStream('auto', 'https://swr-swr2-live.cast.addradio.de/swr/swr2/live/aac/128/stream.aac')

    def play(self, mediaIndex = None):
        if self.live:
            mediaPlayer = monomedia.player.getPlayer()(self.getLiveStream())
        else:
            mediaPlayer = monomedia.player.getPlayer()(self.playlist.getStream(mediaIndex)[1])

        mediaPlayer.play()

    def load(self):
        # later take from https://www.swr.de/~webradio/swr2/swr2-playerbar-102~playerbarContainer.json
        if self.live:
            return True
        else:
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
                    clipLength=item.format_duration()
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
