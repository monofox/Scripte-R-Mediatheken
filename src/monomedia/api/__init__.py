#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8:ts=4:sw=4:sta:et:sts=4:fdm=marker:ai

__all__ = ['MediaBackend', 'Player']

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
        raise Exception("Loading of data must be implemented")

    def hasSelection(self):
        raise Exception("hasSelection function must be implemented.")

    def printSelection(self):
        raise Exception("printSelection function must be implemented.")

    def getLiveStream(self):
        if self.live:
            raise Exception("Media backend seems to support live stream, but did not implemented it.")
        else:
            raise Exception("Media backend does not support live streams!")

    def play(self):
        raise Exception("play function must be implemented.")

    @staticmethod
    def isResponsible(url, live=False):
        raise Exception("Important interface function not implemented.")

class Signal(object):

    def __init__(self, name):
        self.name = name
        self.observer = []

    def emit(self, *args, **kwargs):
        for itm in self.observer:
            try:
                itm(self.name, *args, **kwargs)
            except Exception as e:
                #print(str(e))
                #pass
                raise e

    def __len__(self):
        return len(self.observer)

    def __call__(self, *args, **kwargs):
        return self.emit(*args, **kwargs)

    def __iadd__(self, item):
        if not item in self.observer:
            self.observer.append(item)
        return self

    def __isub__(self, item):
        try:
            self.observer.remove(item)
        except:
            pass
        return self

class Player(object):
    
    def __init__(self, *args, **kwargs):
        self.items = []
        for i in args:
            self.items.append(i)

    def play(self):
        raise Exception("Abstract class. Please choose the right one.")

