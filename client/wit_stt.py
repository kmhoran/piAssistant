#!/usr/bin/env python2
# -*- coding: utf-8-*-
import os
import wave
import json
import tempfile
import logging
import urllib
import urlparse
import re
import subprocess
from abc import ABCMeta, abstractmethod
import requests
import yaml
import jasperpath
import diagnose
import vocabcompiler


class WitAiEngine(object):
    """
    Generic parent class for all STT engines
    """

    def __init__(self):
        self.config = self.get_config() 
        self._logger = logging.getLogger(__name__)
        self.token = self.config['access_token']
        self.set_headers()



    def set_headers(self):
        
        self._headers = {'Authorization': 'Bearer %s' % self.token,
                         'accept': 'application/json',
                         'Content-Type': 'audio/wav'}

    @property
    def headers(self):
        return self._headers

    def get_config(self):
        # FIXME: Replace this as soon as we have a config module
        config = {}
        # Try to get wit.ai Auth token from config
        profile_path = jasperpath.config('profile.yml')
        if os.path.exists(profile_path):
            with open(profile_path, 'r') as f:
                profile = yaml.safe_load(f)
                if 'witai-stt' in profile:
                    if 'access_token' in profile['witai-stt']:
                        config['access_token'] = \
                            profile['witai-stt']['access_token']
        print(config)
        return config


    def get_instance(self):
        #config = self.get_config()
        #instance = self(**config)
        #return instance
        return self

    def get_passive_instance(self):
        return self.get_active_instance()

    def get_active_instance(self):
        return self.get_instance()

    def is_available(cls):
        return diagnose.check_network_connection()

    def is_conversation_initiated(self, fp):
        print ("wit_stt >> determining if conversation is initiated")
        transcription = self.transcribe(fp)
        print("wit_stt >> transcribed: {0}".format(transcription))

        if transcription == []:
            return False

        if not transcription.get("outcomes"):
            return False
        outcomes = transcription.get("outcomes")

        if not outcomes[0].get("entities"):
            print("wit_stt >>  no entities")
            return False
        entities = outcomes[0].get("entities")
        print("wit_stt >> entities: {0}".format(entities))


        if not entities.get("courtesy"):
            print("wit_stt >> no courtesy")
            return False
        courtesy = entities.get("courtesy")
        print("wit_stt >>  courtesy: {0}".format(courtesy[0]))
        if not courtesy[0].get("value"):
            return False
        value = courtesy[0].get("value")
        print("wit_stt >> value = " + value)
        if value == "Greeting":
            print("~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~")
            print("CONVERSATION INITIATED!")
            print("~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~")

        return value == "Greeting"



    def transcribe(self, fp):
        # add   
        print("wit_stt>> Transcribing through wit-ai")
        data = fp.read()
        r = requests.post('https://api.wit.ai/speech?v=20150101',
                          data=data,
                          headers=self.headers)

        ## Let's see the URL we're passing
        # print("This is the URL: " + r.url)
        # print("Here are the headers: " + self.headers)

        try:
            r.raise_for_status()
            response = r.json()
        except requests.exceptions.HTTPError:
            self._logger.critical('Request failed with response: %r',
                                  r.text,
                                  exc_info=True)
            return []
        except requests.exceptions.RequestException:
            self._logger.critical('Request failed.', exc_info=True)
            return []
        except ValueError as e:
            self._logger.critical('Cannot parse response: %s',
                                  e.args[0])
            return []
        except KeyError:
            self._logger.critical('Cannot parse response.',
                                  exc_info=True)
            return []
        else:
            transcribed = ''
            if response:
                transcribed =response
            self._logger.info('Wit.ai response : %r', transcribed)
            return transcribed


"""
class WitAiSTT(AbstractSTTEngine):
    ""
    Speech-To-Text implementation which relies on the Wit.ai Speech API.

    This implementation requires an Wit.ai Access Token to be present in
    profile.yml. Please sign up at https://wit.ai and copy your instance
    token, which can be found under Settings in the Wit console to your
    profile.yml:
        ...
        stt_engine: witai
        witai-stt:
          access_token:    ERJKGE86SOMERANDOMTOKEN23471AB
    ""

    SLUG = "witai"

    def __init__(self, access_token):
        self._logger = logging.getLogger(__name__)
        self.token = access_token

    @classmethod
    def get_config(self):
        # FIXME: Replace this as soon as we have a config module
        config = {}
        # Try to get wit.ai Auth token from config
        profile_path = jasperpath.config('profile.yml')
        if os.path.exists(profile_path):
            with open(profile_path, 'r') as f:
                profile = yaml.safe_load(f)
                if 'witai-stt' in profile:
                    if 'access_token' in profile['witai-stt']:
                        config['access_token'] = \
                            profile['witai-stt']['access_token']
        return config

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, value):
        self._token = value
        self._headers = {'Authorization': 'Bearer %s' % self.token,
                         'accept': 'application/json',
                         'Content-Type': 'audio/wav'}

    @property
    def headers(self):
        return self._headers

    def transcribe(self, fp):
        data = fp.read()
        r = requests.post('https://api.wit.ai/speech?v=20150101',
                          data=data,
                          headers=self.headers)

        ## Let's see the URL we're passing
        # print("This is the URL: " + r.url)
        # print("Here are the headers: " + self.headers)

        try:
            r.raise_for_status()
            text = r.json()['_text']
        except requests.exceptions.HTTPError:
            self._logger.critical('Request failed with response: %r',
                                  r.text,
                                  exc_info=True)
            return []
        except requests.exceptions.RequestException:
            self._logger.critical('Request failed.', exc_info=True)
            return []
        except ValueError as e:
            self._logger.critical('Cannot parse response: %s',
                                  e.args[0])
            return []
        except KeyError:
            self._logger.critical('Cannot parse response.',
                                  exc_info=True)
            return []
        else:
            transcribed = []
            if text:
                transcribed.append(text.upper())
            self._logger.info('Transcribed: %r', transcribed)
            return transcribed

    @classmethod
    def is_available(cls):
        return diagnose.check_network_connection()


def get_engine_by_slug(slug=None):
    ""
    Returns:
        An STT Engine implementation available on the current platform

    Raises:
        ValueError if no speaker implementation is supported on this platform
    ""

    if not slug or type(slug) is not str:
        raise TypeError("Invalid slug '%s'", slug)

    selected_engines = filter(lambda engine: hasattr(engine, "SLUG") and
                              engine.SLUG == slug, get_engines())
    if len(selected_engines) == 0:
        raise ValueError("No STT engine found for slug '%s'" % slug)
    else:
        if len(selected_engines) > 1:
            print(("WARNING: Multiple STT engines found for slug '%s'. " +
                   "This is most certainly a bug.") % slug)
        engine = selected_engines[0]
        if not engine.is_available():
            raise ValueError(("STT engine '%s' is not available (due to " +
                              "missing dependencies, missing " +
                              "dependencies, etc.)") % slug)
        return engine
"""

def get_engine():
    return WitAiEngine()
