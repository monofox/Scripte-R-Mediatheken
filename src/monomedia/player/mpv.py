#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8:ts=4:sw=4:sta:et:sts=4:fdm=marker:ai

import monomedia.api
from python_mpv_jsonipc import MPV
import time
import logging
import logging.handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger()
log.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
log.addHandler(ch)

class MpvPlayer(monomedia.api.Player):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.sigSpeedChanged = monomedia.api.Signal('speed')
        self.sigPathChanged = monomedia.api.Signal('path')
        self.sigPlaybackAbort = monomedia.api.Signal('playback-abort')
        self.sigStartFile = monomedia.api.Signal('start-file')
        self.sigResume = monomedia.api.Signal('resume')
        self.sigPause = monomedia.api.Signal('pause')
        self.sigPlayerStart = monomedia.api.Signal('player-start')
        self.sigPlayerEnd = monomedia.api.Signal('player-end')
        self.sigPlaybackTimeChanged = monomedia.api.Signal('playback-time')

    def play(self):
        mpv = MPV()

        @mpv.property_observer("speed")
        def onSpeedChanged(name, value):
            self.sigSpeedChanged(value)

        @mpv.property_observer("path")
        def onPathChanged(name, value):
            self.sigPathChanged(value)

        @mpv.property_observer("playback-abort")
        def onPlaybackAbortChanged(name, value):
            self.sigPlaybackAbort(value)

        @mpv.on_event('start-file')
        def onFileStartEvent(event_data):
            self.sigStartFile(event_data['playlist_entry_id'] - 1)

        @mpv.on_event('playback-restart')
        @mpv.on_event('unpause')
        def onResumeEvent(event_data):
            self.sigResume()

        @mpv.on_event('pause')
        def onPauseEvent(event_data):
            self.sigPause()

        self.sigPlayerStart()

        i = 0
        for stream in self.items:
            i += 1
            log.info('Loading track #{:d}'.format(i))
            mpv.loadfile(stream.stream, 'append-play')

        running = True
        while running:
            time.sleep(1.0)
            try:
                currentPlaybackPosition = mpv.command('get_property', 'playback-time')
            except BrokenPipeError as e:
                log.error('MPV died. Stopping playback.')
                self.sigPlaybackAbort()
                running = False
            else:
                self.sigPlaybackTimeChanged(currentPlaybackPosition)

        self.sigPlayerEnd()
