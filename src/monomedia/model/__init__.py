#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8:ts=4:sw=4:sta:et:sts=4:fdm=marker:ai

__all__ = ['Playlist', 'PlaylistItem', 'PlaylistItemStream']

class Playlist(list):
    
    def getStream(self, mediaIndex):
        assert mediaIndex != None

        if mediaIndex == -1:
            return True
        else:
            i = 0
            for item in self:
                for stream in item:
                    if i == mediaIndex:
                        return stream
                    i += 1
            return False

class PlaylistItem(list):
    
    def __init__(self, title):
        self.title = title
    
    def append(self, *args, **kwargs):
        super().append(*args, **kwargs)
        self.sort()

class PlaylistItemStream(object):
    
    QUALITY_AUTO = 'auto'
    QUALITY_LQ = 'LQ'
    QUALITY_MQ = 'MQ'
    QUALITY_HQ = 'HQ'
    QUALITY_EQ = 'EQ'
    QUALITY_HD = 'HD'
    QUALITY_SQ = 'SQ'
    
    SEQ_QUALITY = [QUALITY_AUTO, QUALITY_LQ, QUALITY_MQ, QUALITY_HQ, \
        QUALITY_EQ, QUALITY_HD, QUALITY_SQ]
    
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
