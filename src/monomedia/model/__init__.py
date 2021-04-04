#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8:ts=4:sw=4:sta:et:sts=4:fdm=marker:ai

__all__ = ['Playlist', 'PlaylistItem', 'PlaylistItemStream']

class Playlist(list):

    def __init__(self, title=None, totalDuration=None):
        self.title = title
        self.totalDuration = totalDuration
    
    def getStream(self, mediaIndex, best=False):
        assert mediaIndex != None

        if mediaIndex == -1:
            return mediaIndex, True
        else:
            i = 0
            j = 0
            for item in self:
                for stream in item:
                    if best and not stream.isBest:
                        j += 1
                        continue
                    if i == mediaIndex:
                        return j, stream
                    i += 1
                    j += 1
            return mediaIndex, False

    @property
    def duration(self):
        if self.totalDuration:
            return self.format_duration(self.totalDuration)
        else:
            return 0

    @staticmethod
    def format_duration(seconds):
        """
        Stole from: http://www.voidcn.com/article/p-qlzvdfdd-c.html
        """
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

class PlaylistItem(list):
    
    def __init__(self, title, totalDuration=None):
        self.title = title
        self.totalDuration = totalDuration

    @property
    def duration(self):
        if self.totalDuration:
            return Playlist.format_duration(self.totalDuration)
        else:
            return 0

    def sort(self, *args, **kwargs):
        super().sort(*args, **kwargs)

        for f in self:
            f.isBest = False
        try:
            self[-1].isBest = True
        except:
            pass

    def isStreamKnown(self, stream):
        for istream in self:
            if istream.stream == stream:
                return True
        return False
    
    def append(self, item, *args, **kwargs):
        if not self.isStreamKnown(item.stream):
            super().append(item, *args, **kwargs)
            self.sort()

class PlaylistItemStream(object):
    
    QUALITY_AUTO = 'auto'
    QUALITY_AUDIO = 'audio'
    QUALITY_LQ = 'LQ' # 360p, 370p
    QUALITY_MQ = 'MQ' # 380p
    QUALITY_HQ = 'HQ' # 540p
    QUALITY_EQ = 'EQ' # 720p
    QUALITY_HD = 'HD' # 740p
    QUALITY_SQ = 'SQ' # 1080p
    QUALITY_XQ = 'XQ' # 2160p
    
    SEQ_QUALITY = [QUALITY_AUTO, QUALITY_AUDIO, QUALITY_LQ, QUALITY_MQ, \
        QUALITY_HQ, QUALITY_EQ, QUALITY_HD, QUALITY_SQ, QUALITY_XQ]
    
    def __init__(self, quality, stream):
        assert quality in self.SEQ_QUALITY

        self.quality = quality
        self.stream = stream

    def __unicode__(self):
        return self.stream.encode('utf-8')

    def __str__(self):
        return self.__unicode__().decode('utf-8')

    def __repr__(self):
        return '<PlaylistItemStream quality="{:s}" stream="{:s}">'.format(
            self.quality,
            self.stream
        )

    def __eq__(self, item):
        return self.quality == item.quality

    def __lt__(self, item):
        return self.SEQ_QUALITY.index(self.quality) < self.SEQ_QUALITY.index(item.quality)

    def __gt__(self, item):
        return self.SEQ_QUALITY.index(self.quality) > self.SEQ_QUALITY.index(item.quality)
