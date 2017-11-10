# -*- coding: utf-8-*-
import os
import re
import twitter
import jasperpath
import yaml

WORDS = ["TRUMP TWEETS"]

class twitter_credentials:
    def __init__(self):
        self.config = self.get_config()


    def get_config(self):
        config = {}
        # try to get twitter credentials from config
        profile_path = jasperpath.config('profile.yml')
        if os.path.exists(profile_path):
            # print
            print('>> profile.yml found')
            with open(profile_path, 'r') as file:
                profile = yaml.safe_load(file)
                if 'twitter' in profile:
                    # print
                    print('>> twitter found in profile')
                    if 'consumer_key' in profile['twitter']:
                        # print
                        print('>> consumer_key found')
                        if 'consumer_secret' in profile['twitter']:
                            # print
                            print('>> consumer secret found!')
                            config['consumer_key'] = \
                                profile['twitter']['consumer_key']
                            config['consumer_secret'] = \
                                profile['twitter']['consumer_secret']
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
