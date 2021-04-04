#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8:ts=4:sw=4:sta:et:sts=4:fdm=marker:ai

from .mpv import MpvPlayer

__all__ = ['getPlayer', 'MpvPlayer']

def getPlayer():
    """Automatically select an appropriate player
    for current system.

    Returns:
        Player: returns auto selected player
    """
    return MpvPlayer

