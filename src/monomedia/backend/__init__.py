#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8:ts=4:sw=4:sta:et:sts=4:fdm=marker:ai

import sys, inspect
from .berphil import BerphilMediaBackend
from .ard import ARDMediaBackend
from .hr2 import Hr2MediaBackend
from .swr2 import Swr2MediaBackend
from .orf2 import Orf2MediaBackend
from .kika import KikaMediaBackend
from .zdf3sat import ZDFMediaBackend, DreiSatMediaBackend

backends = ['BerphilMediaBackend','ARDMediaBackend', 'Hr2MediaBackend', \
    'Swr2MediaBackend', 'KikaMediaBackend', 'ZDFMediaBackend', 'DreiSatMediaBackend', \
    'Orf2MediaBackend']
__all__ = ['getMediaBackend']
__all__ += backends

def getMediaBackend(url, live=False):
    current_module = sys.modules[__name__]
    for mediaBackend in backends:
        mb = getattr(current_module, mediaBackend)
        if mb.isResponsible(url, live):
            return mb(url, live)
    
    return None