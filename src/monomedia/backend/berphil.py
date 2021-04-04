#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8:ts=4:sw=4:sta:et:sts=4:fdm=marker:ai
# 
# Example URL: https://www.digitalconcerthall.com/de/concert/52494
# First get a "playlist" of the works part of the concert: https://www.digitalconcerthall.com/json_services/get_stream_urls?id=52494&language=de
# (relevant is the id 52494). I might be wrong, but seems that there is no real authentication mechanism.
# BUT: with curl, only the second part of the concert is given. Firefox retrieves both. Figured out, it has something to do with the cookie.
# For each work in the get_stream_urls, we can retrieve the CUE points: https://www.digitalconcerthall.com/text_services/get_work_cuepoints?id=52494-1&language=de
# Furthermore for each work we can retrieve the master playlist: https://world-vod.dchdns.net/hlss/dch/52494-1/,h264_LOW_THREE,h264_LOW_TWO,h264_LOW_ONE,h264_MEDIUM_TWO,h264_MEDIUM_ONE,h264_HIGH,h264_VERY_HIGH_ONE,.mp4.urlset/master.m3u8
# And strange is, that there is an "encryption" key: https://world-vod.dchdns.net/hlss/dch/52494-1/h264_VERY_HIGH_ONE.mp4/encryption.key
# User information retrieved via: https://www.digitalconcerthall.com/json_services/get_user (via cookies)
# 
# login done e.g. via curl 'https://www.digitalconcerthall.com/de/login' (POST, data: action=login, username, password)
# Favorites via curl 'https://www.digitalconcerthall.com/json_services/get_favourites' (get)
# Set favorites: https://www.digitalconcerthall.com/json_services/set_favourite?product_id=52428-1
# delete favorite: https://www.digitalconcerthall.com/json_services/set_favourite?product_id=52428-1&remove=true
# some pings are executed frequently: https://www.digitalconcerthall.com/miniscripts/ping.php?token=1de1agp0afg5d8ptlcd9h78kq1 (no idea for what)
# live stream times: https://www.digitalconcerthall.com/json_cacheable_services/get_livestream_times?timezone=Europe%2FBerlin (all!)
# articles (whatever): https://bphil.zendesk.com/api/v2/help_center/de/sections/115000717353/articles.json?per_page=100
# #### AWESOME ####
"""
    json_userGet: '/json_services/get_user',
    newsletterSet: '/json_services/newsletter',
    json_userResendActivationMail: '/json_services/resend_activation_mail',
    json_deviceSet: '/json_services/device',
    json_checkEmail: '/json_services/check_email',
    json_favouriteGet: '/json_services/get_favourites',
    json_favouriteSet: '/json_services/set_favourite',
    json_getLivestreamTimes: '/json_cacheable_services/get_livestream_times',
    json_getTimezones: '/json_cacheable_services/get_timezones',
    json_setTimezone: '/json_services/set_timezone',
    json_getInstitutionForClient: '/json_services/get_institution_for_client',
    json_validateInstitutionalAccess: '/json_services/validate_institutional_access',
    json_setInstitutionalAccess: '/json_services/set_institutional_access',
    json_logDirectAccessAccepted: '/json_services/log_direct_access_accepted',
    streamlogTracking: 'https://api.digitalconcerthall.com/streamlog.php',
    json_getArtistFilter: '/json_cacheable_services/get_artist_filter',
    json_getStates: '/json_cacheable_services/get_states',
    vtt_getWorkCuepoints: '/text_services/get_work_cuepoints',
    vtt_getWorkCaptions: '/text_services/get_work_captions',
    json_getStreamUrls: '/json_services/get_stream_urls',
    pingUrl: '/miniscripts/ping.php',
    media_playerIntroDe: '//www.digitalconcerthall.com/concerthall/intro/logo_animation_nosony_de_400kbps.mp4',
    media_playerIntroEn: '//www.digitalconcerthall.com/concerthall/intro/logo_animation_nosony_en_400kbps.mp4',
    json_getSearchAutosuggestBase: '//www.digitalconcerthall.com/cms/cachedcontent/',
"""
# Secret (Production):
# apiKey = <censored>
# apiSecret = <censored> (obfuscated)
# baseUrl = https://api.digitalconcerthall.com/v1.2
# baseUrlV2 = https://api.digitalconcerthall.com/v2/
# thumbnailBaseUrl = https://www.digitalconcerthall.com/cms/thumbnails
# manifestV2Url = https://api.digitalconcerthall.com/v2/manifest
# textEndpoint = https://api.digitalconcerthall.com/v2/text/
# countriesUrl = https://api.digitalconcerthall.com/v2/countries
# authentication via oauth2 (working with token) https://api.digitalconcerthall.com/v2/oauth2/token?
# 		client_secret				<censored> (obfuscated)
# 		app_id						com.novoda.dch 		=> dch.android
# 		device_vendor				Google
# 		affiliate					google-mobile
# 		app_version					v2.5.0-0-google
# 		device_model				Pixel 10
# 		app_distributor				google-play
# 		grant_type					device
# Lets sign in via oauth2:
# 		username 					<username>
# 		password 					<password>
# 		grant_type 					password
# Get user information:
# 		curl -v 'https://api.digitalconcerthall.com/v2/user' -H 'Accept: application/json' -H 'Cache-Control: no-cache' -H 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6ImViNGQxZGIyYjkxNDU4MzE1ZGY4YmIzZjBkMGQ3MjE1MzFiNjczNjgxYWI2NmY5M2NmZTVmZjYxNDhkZGNlOWIzMTkyMjIyMjNmNTM3ZjVmIn0.eyJhdWQiOiJkY2guYW5kcm9pZCIsImp0aSI6ImViNGQxZGIyYjkxNDU4MzE1ZGY4YmIzZjBkMGQ3MjE1MzFiNjczNjgxYWI2NmY5M2NmZTVmZjYxNDhkZGNlOWIzMTkyMjIyMjNmNTM3ZjVmIiwiaWF0IjoxNTcyMDMzMjQzLCJuYmYiOjE1NzIwMzMyNDMsImV4cCI6MTU4Nzg0NDQ0Mywic3ViIjoiIiwic2NvcGVzIjpbXX0.mdwfUSTkkA1BVMHXswkOGeS2afC8XRSiZkENguDhiZUzc1V9T-9pwdSshNxbgaRbkUwYQt8rSe33FKpi1cgTHOfBsvIa-HkF6VYhB8CYirFkWYdj3Di1BxF011GgSKpsIVeeO0jFmzetZRiL0vtzY9s8gB4bNlHZHWuVBhtEq-8' -XGET
# Concert info: (Accept-Language set to de,en to receive german text, here you find everything!!)
# 		curl -v 'https://api.digitalconcerthall.com/v2/concert/52501' -H 'Accept: application/json' -H 'Accept-Language: de,en' -H 'Cache-Control: no-cache' -H 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6ImViNGQxZGIyYjkxNDU4MzE1ZGY4YmIzZjBkMGQ3MjE1MzFiNjczNjgxYWI2NmY5M2NmZTVmZjYxNDhkZGNlOWIzMTkyMjIyMjNmNTM3ZjVmIn0.eyJhdWQiOiJkY2guYW5kcm9pZCIsImp0aSI6ImViNGQxZGIyYjkxNDU4MzE1ZGY4YmIzZjBkMGQ3MjE1MzFiNjczNjgxYWI2NmY5M2NmZTVmZjYxNDhkZGNlOWIzMTkyMjIyMjNmNTM3ZjVmIiwiaWF0IjoxNTcyMDMzMjQzLCJuYmYiOjE1NzIwMzMyNDMsImV4cCI6MTU4Nzg0NDQ0Mywic3ViIjoiIiwic2NvcGVzIjpbXX0.mdwfUSTkkA1BVMHXswkOGeS2afC8XRSiZkENguDhiZUzc1V9T-9pwdSshNxbgaRbkUwYQt8rSe33FKpi1cgTHOfBsvIa-HkF6VYhB8CYirFkWYdj3Di1BxF011GgSKpsIVeeO0jFmzetZRiL0vtzY9s8gB4bNlHZHWuVBhtEq-8' -XGET
# Structure BerPhil
# Film
# Concert
#   Work
#       CuePoints
#   Interview


from monomedia.api import MediaBackend
from monomedia.model import Playlist, PlaylistItem, PlaylistItemStream
import monomedia.player

import urllib.parse
import requests
import json
import sys
import shlex
import subprocess
import os
import getpass
import datetime
import queue
import threading
import re
import telnetlib
import time
import hashlib
import math
import socket
import tempfile
import select
from python_mpv_jsonipc import MPV
import logging

class BerPhilStream(PlaylistItemStream):

    def __init__(self, mediaId=None, fragmentId=None, streamType=None, \
        audioLanguage=None, videoLanguage=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mediaId = mediaId
        self.fragmentId = fragmentId
        self.streamType = streamType
        self.audioLanguage = audioLanguage
        self.videoLanguage = videoLanguage

    @staticmethod
    def _convertQuality(quality):
        mapper = {
            'AUDIO': PlaylistItemStream.QUALITY_AUDIO,
            'LOW_THREE': PlaylistItemStream.QUALITY_LQ, 
            'LOW_TWO': PlaylistItemStream.QUALITY_LQ, 
            'LOW_ONE': PlaylistItemStream.QUALITY_MQ, 
            'MEDIUM_TWO': PlaylistItemStream.QUALITY_HQ, 
            'MEDIUM_ONE': PlaylistItemStream.QUALITY_EQ, 
            'HIGH': PlaylistItemStream.QUALITY_HD, 
            'VERY_HIGH_ONE': PlaylistItemStream.QUALITY_SQ, 
            'ULTRA_HIGH': PlaylistItemStream.QUALITY_XQ
        }
        
        try:
            return mapper[quality]
        except KeyError:
            return PlaylistItemStream.QUALITY_AUTO

    @classmethod
    def createFromJson(bps, mediaId, jsobj):
        quality = bps._convertQuality(jsobj['quality'])
        self = bps(
            mediaId=mediaId,
            audioLanguage=jsobj['audio_language'],
            videoLanguage=jsobj['video_language'],
            quality=quality,
            stream=jsobj['url']
        )

        return self

class BerPhilCuePoint(object):

    @classmethod
    def createFromJson(bpcp, jsobj):
        self = bpcp()
        self.duration = jsobj['duration']
        self.time = jsobj['time']
        self.text = jsobj['text']

        return self

class BerPhilMedia(PlaylistItem):

    def __init__(self):
        self._streamEndpoint = None

        self.id = None
        self.isFree = False
        self.title = None
        self.type = None
        self.shortDescription = None
        self.programme = None
        self.worksIntroduction = None
        self.totalDuration = None
        self.maxResolution = None
        self.copyright = None
        self.artistBiographies = None
        self.trailerUrls = {}
        self.images = {}
        self.imageCredit = None
        self.updated = None
        self.beginDate = None
        self.endDate = None
        self.publishedDate = None

        self.streamList = None

    def fetchStreams(self, bps):
        # does it have an endpoint?
        if self._streamEndpoint:
            self.streamList = bps.getStreams(self._streamEndpoint)

    @staticmethod
    def createDate(jsobj, dateType):
        if 'date' not in jsobj.keys() or dateType not in jsobj['date'].keys():
            return None

        return datetime.datetime.fromtimestamp(jsobj['date'][dateType])

    @classmethod
    def createFromJson(bpm, jsobj):
        self = bpm()
        self.id = jsobj['id']
        self.isFree = jsobj['is_free']
        self.title = jsobj['title']
        self.type = jsobj['type'] if 'type' in jsobj.keys() else None
        self.totalDuration = jsobj['duration_total'] if 'duration_total' in jsobj.keys() else None
        self.maxResolution = jsobj['max_resolution']
        self.copyright = jsobj['copyright']
        self.imageCredit = jsobj['image_credit']
        self.updated = datetime.datetime.fromtimestamp(jsobj['updated'])
        self.images = jsobj['image']
        self.beginDate = self.createDate(jsobj, 'begin')
        self.endDate = self.createDate(jsobj, 'end')
        self.publishedDate = self.createDate(jsobj, 'published')

        # check for references (e.g. stream endpoint)
        if '_links' in jsobj.keys():
            if 'streams' in jsobj['_links'].keys():
                self._streamEndpoint = jsobj['_links']['streams']['href']

        return self

class BerPhilMediaItem(PlaylistItem):

    def __init__(self, id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = id
        self.cuepoints = []
        self._streamEndpoint = None

    def fetchStreams(self, bps):
        # does it have an endpoint?
        if self._streamEndpoint:
            self += bps.getStreams(self.id, self._streamEndpoint)
            self.sort()

    @staticmethod
    def createDate(jsobj, dateType):
        if 'date' not in jsobj.keys() or dateType not in jsobj['date'].keys():
            return None

        return datetime.datetime.fromtimestamp(jsobj['date'][dateType])

    @classmethod
    def createFromJson(bpw, jsobj):
        self = bpw(jsobj['id'], jsobj['title'])
        self.isHighlight = jsobj['is_highlight'] if 'is_highlight' in jsobj else False
        self.isFree = jsobj['is_free']
        try:
            self.totalDuration = jsobj['duration']
        except:
            self.totalDuration = 0
        self.composerName = jsobj['name_composer'] if 'name_composer' in jsobj else None
        self.beginDate = self.createDate(jsobj, 'begin')
        self.endDate = self.createDate(jsobj, 'end')
        self.publishedDate = self.createDate(jsobj, 'published')
        if 'cuepoints' in jsobj.keys() and jsobj['cuepoints']:
            for cp in jsobj['cuepoints']:
                self.cuepoints.append(BerPhilCuePoint.createFromJson(cp))

        # check for references (e.g. stream endpoint)
        if '_links' in jsobj.keys():
            if 'streams' in jsobj['_links'].keys():
                self._streamEndpoint = jsobj['_links']['streams']['href']

        return self


class BerPhilInterview(BerPhilMediaItem):
    pass

class BerPhilInterviewWrapper(Playlist):

    def fetchStreams(self, bps):
        for p in self:
            p.fetchStreams(bps)

    @classmethod
    def createFromJson(bpi, jsobj):
        self = bpi()
        self.isFree = jsobj['is_free']
        self.shortDescription = jsobj['short_description']
        self.title = jsobj['title']
        self.totalDuration = jsobj['duration']
        self.append(BerPhilInterview.createFromJson(jsobj))
        return self

class BerPhilWork(BerPhilMediaItem):
    pass

class BerPhilFilm(Playlist):

    def fetchStreams(self, bps):
        for p in self:
            p.fetchStreams(bps)

    @classmethod
    def createFromJson(bpi, jsobj):
        self = bpi()
        self.isFree = jsobj['is_free']
        self.shortDescription = jsobj['short_description']
        self.title = jsobj['title']
        self.totalDuration = jsobj['duration']
        self.append(BerPhilMediaItem.createFromJson(jsobj))
        return self

class BerPhilConcert(Playlist):

    def __init__(self, id, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.concertId = id
        self.isFree = False
        self.trailers = {}
        self.artistBiographies = None
        self.program = []

    def fetchStreams(self, bps):
        for p in self:
            p.fetchStreams(bps)

    @classmethod
    def createFromJson(bpc, jsobj):
        id = jsobj['id']

        self = bpc(id, jsobj['title'], jsobj['duration_total'])
        self.isFree = jsobj['is_free']
        self.artistBiographies = jsobj['artist_biographies']
        self.programme = jsobj['programme']
        self.worksIntroduction = jsobj['works_introduction']
        self.shortDescription = jsobj['short_description']
        self.trailers = {
            'HD': jsobj['trailer_url_hd'],
            'SD': jsobj['trailer_url_sd']
        }

        # is there anything embedded?
        if '_embedded' in jsobj.keys():
            for programType in jsobj['_embedded'].keys():
                for work in jsobj['_embedded'][programType]:
                    className = 'BerPhil' + programType.capitalize()
                    if className not in globals().keys():
                        raise Exception('Does not know how to handle program type ' + programType)
                    creationMethod = getattr(globals()[className], 'createFromJson')
                    self.append(creationMethod(work))
                self.sort(key=lambda x: x.id)

        return self

class BerPhilSession(object):
    MEDIA_TYPE_CONCERT = 'concert'
    MEDIA_TYPE_FILM = 'film'
    MEDIA_TYPE_INTERVIEW = 'interview'

    def __init__(self):
        self._apiBaseUrl = 'https://api.digitalconcerthall.com/v2'
        self._apiOfferUrl = 'https://apps.digitalconcerthall.com/offers.json'
        self._apiStreamlog = 'https://api.digitalconcerthall.com/streamlog.php'
        # device client token
        self._clientTokenType = None
        self._clientToken = None
        self._clientRefreshToken = None
        self._clientTokenTime = None
        self._clientTokenExpires = None
        # client secret
        self._clientSecret = None
        self._clientApiKey = None
        self._log = logging.getLogger(__name__)

    def _parseTypeAndId(self, url):
        ux = urllib.parse.urlsplit(url)
        if not ux.path:
            raise Exception('No path available in URL to extract concert ID')

        pathFragments = ux.path.split('/')
        pathFragments.reverse()

        # min. 2 elements are required.
        if len(pathFragments) < 2:
            raise Exception('Invalid URI to DCH media given.')

        if pathFragments[1] not in [self.MEDIA_TYPE_INTERVIEW, self.MEDIA_TYPE_FILM, self.MEDIA_TYPE_CONCERT]:
            raise Exception('DCH media type ' + pathFragments[1] + ' unknown.')

        return (pathFragments[1], pathFragments[0])

    def setSecret(self, secret, apiKey):
        self._clientSecret = secret
        self._clientApiKey = apiKey

    def getAppInformation(self):
        return {
            'app_id': 'dch.android',
            'app_version': 'v2.5.0-0-google',
            'app_distributor': 'google-play'
        }

    def getDeviceInformation(self):
        return {
            'device_vendor': 'Google',
            'device_model': 'Pixel 10'
        }

    def _setToken(self, tokenJson):
        if tokenJson:
            self._clientToken = tokenJson['access_token']
            self._clientTokenExpires = tokenJson['expires_in']
            self._clientRefreshToken = tokenJson['refresh_token']
            self._clientTokenType = tokenJson['token_type']
            self._clientTokenTime = datetime.datetime.now()
            if 'pin' in tokenJson:
                self._clientTokenPin = tokenJson['pin']
        else:
            self._clientToken = None
            self._clientTokenType = None
            self._clientTokenTime = None

    def _getClientToken(self, clientSecret=None):
        # token already known and still valid?
        if self._clientToken and datetime.datetime.now() < (self._clientTokenTime + datetime.timedelta(seconds=self._clientTokenExpires)):
            return self._clientToken
        # FIXME: refresh
        # If token is expired, we need to re-request (thats why we save the refresh token). 
        # In case, we know already username + password, we shall auto-login.

        # if clientSecret is not given as parameter, take from login.
        if clientSecret is None:
            clientSecret = self._clientSecret

        # if the _clientSecret is not available, the user didn't logged in yet.
        if not clientSecret:
            raise Exception('No secret known yet... Oh no!!')

        oauth2TokenUri = self._apiBaseUrl + '/oauth2/token'
        data = {
            'grant_type': 'device',
            'client_secret': clientSecret, # <<< this is top-secret (but was easy to figure out). 
            # Altough my opinion is that the security must be done on server side, i better do not publish 
            # this "secret" key.
            'affiliate': 'google-mobile'
        }
        data.update(self.getAppInformation())
        data.update(self.getDeviceInformation())
        hdr = {
            'Accept': 'application/json',
            'Accept-Language': 'de, en',
            'Cache-Control': 'no-cache'
        }
        r = requests.post(oauth2TokenUri, data=data, headers=hdr, allow_redirects=True)
        if not r:
            self._setToken(None)
            raise Exception('Could not fetch a device token.')
        else:
            self._setToken(r.json())

        return self._clientToken

    def signIn(self, username, password):
        token = self._getClientToken()
        oauth2TokenUri = self._apiBaseUrl + '/oauth2/token'
        data = {
            'grant_type': 'password',
            'username': username,
            'password': password
        }
        hdr = {
            'Accept': 'application/json',
            'Accept-Language': 'de, en',
            'Cache-Control': 'no-cache',
            'Authorization': 'Bearer ' + token
        }
        r = requests.post(oauth2TokenUri, data=data, headers=hdr, allow_redirects=True)
        if r:
            # this is now overwriting the regular token!
            self._setToken(r.json())
            self._user = self.getUser()
            return True
        else:
            self._setToken(None)
            return False

    def getToken(self):
        # FIXME: check what to do and either execute regular client token or signin (to avoid loop).
        return self._getClientToken()

    def updateDeviceInformation(self):
        token = self.getToken()
        data = {
            'affiliate': 'google-mobile',
        }
        data.update(self.getAppInformation())
        data.update(self.getDeviceInformation())
        hdr = {
            'Accept': 'application/json',
            'Accept-Language': 'de, en',
            'Cache-Control': 'no-cache',
            'Authorization': 'Bearer ' + token
        }
        r = requests.post(self._apiBaseUrl + '/device', data=data, headers=hdr)
        if r:
            return r.json()
        else:
            raise Exception('Could not update device information.')

    def getUser(self):
        token = self.getToken()
        hdr = {
            'Accept': 'application/json',
            'Accept-Language': 'de, en',
            'Cache-Control': 'no-cache',
            'Authorization': 'Bearer ' + token
        }
        r = requests.get(self._apiBaseUrl + '/user', headers=hdr)
        if r:
            return r.json()
        else:
            raise Exception('Could not retrieve any user information. Are you logged in?')

    def getFavourites(self):
        token = self.getToken()
        hdr = {
            'Accept': 'application/json',
            'Accept-Language': 'de, en',
            'Cache-Control': 'no-cache',
            'Authorization': 'Bearer ' + token
        }
        r = requests.get(self._apiBaseUrl + '/user/favourites', headers=hdr)
        if r:
            return r.json()
        else:
            raise Exception('Could not retrieve any user favourites. Are you logged in?')

    def _updateFavourite(self, action, mediaId):
        token = self.getToken()
        data = {
            'action': action,
            'id': mediaId
        }
        hdr = {
            'Accept': 'application/json',
            'Accept-Language': 'de, en',
            'Cache-Control': 'no-cache',
            'Authorization': 'Bearer ' + token
        }
        r = requests.post(self._apiBaseUrl + '/user/favourites', headers=hdr, json=data)
        if r:
            return r.json()
        else:
            raise Exception('Could not update favourites. Are you logged in?')

    def addFavourite(self, mediaId):
        return self._updateFavourite('add', mediaId)

    def removeFavourite(self, mediaId):
        return self._updateFavourite('remove', mediaId)

    def getOffers(self):
        hdr = {
            'Accept': 'application/json',
            'Accept-Language': 'de, en',
            'Cache-Control': 'no-cache'
        }
        r = requests.get(self._apiOfferUrl, headers=hdr)
        if r:
            return r.json()
        else:
            raise Exception('Could not retrieve any offers.')

    def getClientInfo(self):
        token = self.getToken()
        hdr = {
            'Accept': 'application/json',
            'Accept-Language': 'de, en',
            'Cache-Control': 'no-cache',
            'Authorization': 'Bearer ' + token
        }

        r = requests.get(self._apiBaseUrl + '/client_info', headers=hdr)
        if r:
            return r.json()
        else:
            raise Exception('Could not retrieve client information.')

    def _getMedia(self, mediaType, mediaId):
        # https://api.digitalconcerthall.com/v2/mediaType/mediaId
        concertEndpoint = self._apiBaseUrl + '/' + mediaType + '/' + mediaId
        token = self.getToken()
        hdr = {
            'Accept': 'application/json',
            'Accept-Language': 'de, en',
            'Cache-Control': 'no-cache',
            'Authorization': 'Bearer ' + token
        }
        r = requests.get(concertEndpoint, headers=hdr)
        if r:
            return r.json()
        else:
            raise Exception('Could not retrieve concert info.')

    def getMedia(self, url):
        mediaType, mediaId = self._parseTypeAndId(url)
        tx = self._getMedia(mediaType, mediaId)
        className = 'BerPhil' + mediaType.capitalize()
        if className not in globals().keys():
            raise Exception('Media not known: ' + mediaType)
        
        if className == 'BerPhilInterview':
            className += 'Wrapper'
        createMethod = getattr(globals()[className], 'createFromJson')
        mediaObj = createMethod(tx)
        mediaObj.fetchStreams(self)

        return mediaObj

    def getConcert(self, mediaId):
        return self._getMedia('concert', mediaId)

    def getFilm(self, mediaId):
        return self._getMedia('film', mediaId)

    def getInterview(self, mediaId):
        return self._getMedia('interview', mediaId)

    def getPlaylist(self, mediaId):
        return self._getMedia('playlist', mediaId)

    def getStreams(self, mediaId, endpoint):
        def buildStreamList(jsobj):
            streams = []
            for streamData in jsobj['channel'].values():
                for stream in streamData['stream']:
                    streams.append(BerPhilStream.createFromJson(mediaId, stream))
            return streams

        token = self.getToken()
        if endpoint.startswith('//'):
            endpoint = 'https:' + endpoint
        hdr = {
            'Accept': 'application/json',
            'Accept-Language': 'de, en',
            'Cache-Control': 'no-cache',
            'Authorization': 'Bearer ' + token
        }
        r = requests.get(endpoint, headers=hdr)
        if r:
            return buildStreamList(r.json())
        else:
            raise Exception('Could not retrieve concert info.')

    def sendHeartbeat(self, mediaId, playbackPosition, watchingDuration):
        ts = int(time.time())
        hmd5 = hashlib.new('MD5')
        hmd5.update('{apikey}{uid:d}{ts:d}'.format(
                apikey=self._clientApiKey,
                uid=self._user['uid'],
                ts=ts
            ).encode('utf-8')
        )
        pingHash = hmd5.hexdigest()
        data = {
            'uid': self._user['uid'],
            'ts': ts,
            'pos': playbackPosition,
            'dur': watchingDuration,
            'productid': mediaId,
            'app_id': self.getAppInformation()['app_id'],
            'device_vendor': self.getDeviceInformation()['device_vendor'],
            'hash': pingHash,
            #'offline': 0
        }
        hdr = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept-Language': 'de, en',
            'Cache-Control': 'no-cache',

        }
        self._log.debug('Heartbeat sent to {:s} with content {:s}'.format(self._apiStreamlog, json.dumps(data)))
        r = requests.post(self._apiStreamlog, data=data, headers=hdr)
        if r.status_code != 200:
            self._log.error('Could not sent heartbeat to {:s}, code: {:d}'.format(self._apiStreamlog, r.status_code))
            return False
        else:
            self._log.info('Heartbeat successful.')
            return True

class BerPhilTrackerCmd(object):

    def __init__(self, cmd):
        self.cmd = cmd

    @classmethod
    def heartbeat(bptc, mediaId, streamPos, watchingDuration):
        self = bptc('heartbeat')
        self.mediaId = mediaId
        self.pos = int(round(streamPos, 0))
        self.dur = int(round(watchingDuration, 0))

        return self

    @classmethod
    def terminate(bptc):
        self = bptc('terminate')
        return self

class BerPhilTrackerTransmitter(threading.Thread):
    """Track listening/displaying of concerts / programs.

    streamlog.php/tracker required to inform about the listened
    minutes (needs to be updated every played minute).
    The stream position as well as duration is tracked by the corresponding
    player backend (e.g. BerPhilPlayerMPV).
    Ber Phil Media GmbH requires it in order to pay the right people.
    We cache and send the data via BerPhilSession to the streamlog.php.
    """

    def __init__(self, msgQueue, event, bps):
        super().__init__()
        self._msgQueue = msgQueue
        self._event = event
        self._bps = bps
        self._running = False
        self._pending = []
        self._log = logging.getLogger(__name__)

    def _processQueue(self):
        while self._pending:
            cmdObj = self._pending[0]
            if cmdObj.cmd == 'heartbeat':
                if self._bps.sendHeartbeat(cmdObj.mediaId, cmdObj.pos, cmdObj.dur):
                    self._pending.pop(0)
                else:
                    break

    def run(self):
        self._running = True
        while self._running:
            self._event.wait(timeout=60)
            self._event.clear()
            while True:
                try:
                    cmdObj = self._msgQueue.get_nowait()
                except queue.Empty:
                    break
                if cmdObj:
                    self._log.debug('Received command: {:s}'.format(cmdObj.cmd))
                    if cmdObj.cmd == 'terminate':
                        self._running = False
                    else:
                        self._pending.append(cmdObj)
                else:
                    break
            # try to send the heartbeat
            self._processQueue()
        self._log.info('BerPhilTrackerTransmitter is terminating...')

class BerPhilPlayer(object):

    def __init__(self, bps, *args, **kwargs):
        self._bps = bps
        self._trackerQueue = queue.Queue()
        self._trackerEvents = threading.Event()
        self._trackerThread = None
        self._log = logging.getLogger(__name__)
        self.streamUrls = args

        self.currentTrack = None
        self.playbackStartTime = None
        self.playbackTime = 0.0
        self.playbackDuration = 0.0

    def startTrackerTransmitter(self, *args, **kwargs):
        self._trackerThread = BerPhilTrackerTransmitter(self._trackerQueue, self._trackerEvents, self._bps)
        self._trackerThread.start()

    def terminateTrackerTransmitter(self, *args, **kwargs):
        self._trackerQueue.put(BerPhilTrackerCmd.terminate())
        self._trackerEvents.set()

    def getCurrentPlaybackDuration(self, *args, **kwargs):
        return self.playbackDuration + \
            ((time.time() - self.playbackStartTime) if self.playbackStartTime != None else 0)

    def onPlaybackTimeChanged(self, force=False):
        assert self._trackerThread != None, "Tracker transmitter not started."
        assert self._trackerThread.is_alive(), "Tracker transmitter died?"

        if (self.getCurrentPlaybackDuration() >= 60.0 or force) and self.currentTrack != None \
            and self.playbackTime > 0.0:
            self._log.info('Adding BerPhilTracker: {:s}, at {:.2f} for {:.2f}'.format(
                self.streamUrls[self.currentTrack].mediaId, 
                self.playbackTime, 
                self.getCurrentPlaybackDuration()
            ))
            self._trackerQueue.put(
                BerPhilTrackerCmd.heartbeat(
                    self.streamUrls[self.currentTrack].mediaId, 
                    self.playbackTime, 
                    self.getCurrentPlaybackDuration()
                )
            )
            # rollover to new playback start time.
            self.playbackDuration = 0.0
            self.playbackStartTime = time.time()
            self._trackerEvents.set()

    def setPlaybackTime(self, name, pbtime, *args, **kwargs):
        self.playbackTime = pbtime
        self.onPlaybackTimeChanged()

    def startTrack(self, name, trackId, *args, **kwargs):
        self.stopCurrentTrack()
        self.currentTrack = trackId
        self.playbackTime = 0.0
        self.playbackDuration = 0.0
        self.resumeCurrentTrack()
        self._log.info('Start track #{:d}.'.format(trackId+1))

    def stopCurrentTrack(self, name=None, final=True, *args, **kwargs):
        if self.currentTrack != None:
            endTime = time.time()
            if self.playbackStartTime != None:
                self.playbackDuration += endTime - self.playbackStartTime
                self.playbackStartTime = None
            self.onPlaybackTimeChanged(force=True)
            if final:
                self._log.info('Stopped track #{:d}.'.format(self.currentTrack+1))
            else:
                self._log.info('Paused track #{:d}.'.format(self.currentTrack+1))

    def pauseCurrentTrack(self, *args, **kwargs):
        self.stopCurrentTrack(final=False)

    def resumeCurrentTrack(self, *args, **kwargs):
        self.playbackStartTime = time.time()
        self._log.info('Resuming track #{:d}.'.format(self.currentTrack+1))

    def onPlayerStart(self, *args, **kwargs):
        self.startTrackerTransmitter()

    def onPlayerEnd(self, *args, **kwargs):
        self.terminateTrackerTransmitter()

    def play(self):
        mediaPlayer = monomedia.player.getPlayer()(bps=self._bps, *self.streamUrls)
        mediaPlayer.sigPlaybackAbort += self.stopCurrentTrack
        mediaPlayer.sigStartFile += self.startTrack
        mediaPlayer.sigResume += self.resumeCurrentTrack
        mediaPlayer.sigPause += self.pauseCurrentTrack
        mediaPlayer.sigPlayerStart += self.onPlayerStart
        mediaPlayer.sigPlayerEnd += self.onPlayerEnd
        mediaPlayer.sigPlaybackTimeChanged += self.setPlaybackTime
        mediaPlayer.play()

class BerphilMediaBackend(MediaBackend):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = ''
        self._pwd = ''
        self._secret = ''
        self._apiKey = ''
        self._bps = BerPhilSession()
        self._log = logging.getLogger(__name__)

    def load(self):
        if not self.login():
            self._log.error('User is not authenticated, media cannot be loaded.')
            return False

        self.playlist = self._bps.getMedia(self.media)
        return True

    def play(self, mediaIndex = None):
        if self.live:
            return None

        if mediaIndex is not None and mediaIndex >= 0:
            stream = [self.playlist.getStream(mediaIndex)[1]]
        else:
            stream = []
            for program in self.playlist:
                stream.append(program[-1])

        bpv = BerPhilPlayer(self._bps, *stream)
        bpv.play()

    def printSelection(self, selectDetail=False):
        i = 0

        titleMsg = '{title} ({clipLength})'.format(
            title=self.playlist.title,
            clipLength=self.playlist.duration
        )
        print(titleMsg)
        print('='*len(titleMsg))
        print('This media ' + ('is free.' if self.playlist.isFree else 'requires a ticket.') + \
            os.linesep)

        # now the streams, etc. is handled differently depending on the media type.
        try:
            if self.playlist.shortDescription:
                print(self.playlist.shortDescription + os.linesep)
        except AttributeError:
            pass

        # now each program.
        for item in self.playlist:
            titleMsg = '{title} ({clipLength})'.format(
                title=item.title,
                clipLength=item.duration
            )
            print(titleMsg)
            print('-'*len(titleMsg))
            lastQuality = None
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
            print('')

        print('-1 = play whole program!')
        playNo = input('> ')
        try:
            playNo = int(playNo.strip())
        except ValueError:
            sys.stderr.write('Invalid number given. Quit? Cancel!' + os.linesep)
        else:
            if playNo == -1:
                return playNo
            else:
                playNo, stream = self.playlist.getStream(playNo, not selectDetail)
                if not stream:
                    sys.stderr.write('Stream # does not exist.\n')
                else:
                    return playNo
        return None

    def login(self, username=None, password=None, secret=None, apiKey=None):
        if not username or not password or not secret or not apiKey:
            if not self._checkSettings():
                return False
        else:
            self._user = username
            self._pwd = password
            self._secret = secret
            self._apiKey = apiKey
        self._bps.setSecret(self._secret, self._apiKey)
        return self._bps.signIn(self._user, self._pwd)

    def _checkSettings(self):
        settingsFile = os.path.join(os.path.expanduser('~'), '.berphiluser')
        if os.path.exists(settingsFile):
            settings = None
            with open(settingsFile, 'rb') as f:
                settings = json.loads(f.read().decode('utf-8'))
            if settings:
                self._user = settings['user']
                self._pwd = settings['pwd']
                self._secret = settings['api-secret']
                self._apiKey = settings['api-key']
                return True

        # ask for credentials:
        self._user = input('Username: ')
        if not self._user:
            sys.stderr.write('User aborted login.' + os.linesep)
            return False
        self._pwd = getpass.getpass('Password: ')
        if not self._pwd:
            sys.stderr.write('User aborted login.' + os.linesep)
            return False
        self._secret = getpass.getpass('Client secret (API): ')
        if not self._secret:
            sys.stderr.write('User aborted login.' + os.linesep)
            return False
        self._apiKey = getpass.getpass('Client API Key: ')
        if not self._apiKey:
            sys.stderr.write('User aborted login.' + os.linesep)
            return False

        return True

    def _saveSettings(self):
        data = {
            'user': self._user,
            'pwd': self._pwd,
            'api-secret': self._secret,
            'api-key': self._apiKey
        }

        settingsFile = os.path.join(os.path.expanduser('~'), '.berphiluser')
        with open(settingsFile, 'wb') as f:
            f.write(json.dumps(data).encode('utf-8'))

    def hasSelection(self):
        return not self.live

    @staticmethod
    def isResponsible(url, live=False):
        if 'digitalconcerthall.com' in url:
            return True
        else:
            return False
