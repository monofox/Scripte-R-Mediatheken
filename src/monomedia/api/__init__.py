#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8:ts=4:sw=4:sta:et:sts=4:fdm=marker:ai

__all__ = ['MediaBackend', 'Playlist', 'PlaylistItem', 'PlaylistItemStream', 'Player']

class MediaBackend(object):
    
    def __init__(self, media, live=False):
        self.media = media
        self.live = live
        self.playlist = None

        self.init()

    def setPlaylist(self, playlist):
        self.playlist = playlist

    def init(self):
        pass

    def load(self):
        raise NotImplemented("Loading of data must be implemented")

    def hasSelection(self):
        raise NotImplemented("hasSelection function must be implemented.")

    def printSelection(self):
        raise NotImplemented("printSelection function must be implemented.")

    def getLiveStream(self):
        if self.live:
            raise NotImplemented("Media backend seems to support live stream, but did not implemented it.")
        else:
            raise NotImplemented("Media backend does not support live streams!")

    def play(self):
        raise NotImplemented("play function must be implemented.")

    @staticmethod
    def isResponsible(url, live=False):
        raise NotImplemented("Important interface function not implemented.")

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

class Signal(object):

    def __init__(self, name):
        self.name = name
        self.observer = []

    def emit(self, *args, **kwargs):
        for itm in self.observer:
            try:
                itm(name, *args, **kwargs)
            except Exception:
                pass

    def __len__(self):
        return len(self.observer)

    def __call__(self, *args, **kwargs):
        self.emit(*args, **kwargs)

    def __radd__(self, item):
        if not item in self.observer:
            self.observer.append(item)

    def __rsub__(self, item):
        try:
            self.observer.remove(item)
        except:
            pass

class Player(object):
    
    def __init__(self, *args, **kwargs):
        self.items = []
        for i in args:
            self.items.append(i)

    def play(self):
        raise NotImplemented("Abstract class. Please choose the right one.")

