#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8:ts=4:sw=4:sta:et:sts=4:fdm=marker:ai

from .. import backend
import argparse
import logging
import logging.config
import yaml
import sys
import os

def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Listen and view media of public and non-public broadcasts.\n\n \
    monomedia  Copyright (C) 2021  Lukas Schreiner\n \
    This program comes with ABSOLUTELY NO WARRANTY and is licensed under GPLv3+.\n \
    This is free software, and you are welcome to redistribute it\n \
    under certain conditions; cf. LICENSE file.'
    )
    parser.add_argument('media', type=str, help='URL/stream to media (e.g. from media center).')
    parser.add_argument('--live', action='store_const', const=True, default=False, help='Defines broadcast sender for live stream.')
    parser.add_argument('--select', action='store_const', const=True, default=False, help='Print all available selections.')
    parser.add_argument('--config', type=str, default='logging.yml', help='Defines / specifies log file')
    args = parser.parse_args()

    if args.config:
        try:
            logging.config.dictConfig(yaml.safe_load(open(args.config, 'rb')))
        except FileNotFoundError:
            pass

    mb = backend.getMediaBackend(args.media, args.live)
    if not mb:
        sys.stderr.write('Unknown stream/sender selected.' + os.linesep)
    else:
        # load stream information
        if not mb.load():
            sys.stderr.write('Had trouble during loading media information.' + os.linesep)
        elif mb.hasSelection():
            # encapsulate!
            selection = mb.printSelection(args.select)
            if selection:
                mb.play(selection)
            else:
                sys.stderr.write('Cancelled by user.' + os.linesep)
        else:
            mb.play()
