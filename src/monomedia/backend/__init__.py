#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8:ts=4:sw=4:sta:et:sts=4:fdm=marker:ai

import sys, inspect
from .berphil import BerphilMediaBackend
from .ard import ARDMediaBackend

backends = ['BerphilMediaBackend','ARDMediaBackend']
__all__ = ['getMediaBackend']
__all__ += backends

def getMediaBackend(url, live=False):
    current_module = sys.modules[__name__]
    for mediaBackend in backends:
        mb = getattr(current_module, mediaBackend)
        if mb.isResponsible(url, live):
            return mb(url, live)
    
    return None