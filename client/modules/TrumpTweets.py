# -*- coding: utf-8-*-
import os
import re
import twitter
import jasperpath
import yaml
import base64

WORDS = ["TRUMP TWEETS"]

class twitter_credentials:
    def __init__(self):
        self.config = self.get_config()


    def get_config(self):
        config = {}
        # try to get twitter credentials from config
        profile_path = jasperpath.config('profile.yml')
        if os.path.exists(profile_path):
            with open(profile_path, 'r') as file:
                profile = yaml.safe_load(file)
                if 'twitter' in profile:
                    # Consumer_key and secret are only valid as a pair
                    if 'consumer_key' in profile['twitter']:
                        if 'consumer_secret' in profile['twitter']:
                            config['consumer_key'] = \
                                base64.b64decode(profile['twitter']['consumer_key'])
                            config['consumer_secret'] = \
                                profile['twitter']['consumer_secret']
                    # Token & its secret are non-essential (though very common)
                    # entities in twitter authentication
                    if 'oauth_token' in profile['twitter']:
                        if 'token_secret' in profile['twitter']:
                            config['access_token'] = \
                                profile['twitter']['access_token']
                            config['access_token_secret'] = \
                                profile['twitter']['access_token_secret']
        print("key: %s, secret: %s" % (config['consumer_key'], config['consumer_secret']))
        if 'access_token' in config:
            print("token: %s, secret: %s" % (config['access_token'], config['access_token_secret']))
        return config


def handle(text, mic, profile):
    """
    Reads Donald Trump's latest tweet outloud
    """
    credentials = twitter_credentials()

    mic.say("I'll tell you when I'm good and ready")

def isValid(text):
    """
    Returns true if Jasper hears "Trump Tweets"
    """
    return bool(re.search(r'\btrump\b', text, re.IGNORECASE))
