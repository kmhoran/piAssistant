# -*- coding: utf-8-*-
import re

WORDS = ["SAY"]

def handle(text, mic, profile):
	"""
	Repeats whatever the user says
	"""

	# Let's assume 'say' is the first word of the phrase
	if(len(text) >= 4):
		mic.say(text[4:])
	else:
		mic.say("you want me to say " + text)

def isValid(text):
	"""
	Returns True if Jasper hears the word "Say"
	"""
	return bool(re.search(r'\bsay \b', text, re.IGNORECASE))
