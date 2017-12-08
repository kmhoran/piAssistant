# -*- coding: utf-8-*-
import logging
from notifier import Notifier
from brain import Brain
import random
import sys

class Conversation(object):

    def __init__(self, persona, mic, profile):
        self._logger = logging.getLogger(__name__)
        self.persona = persona
        self.mic = mic
        self.profile = profile
        self.brain = Brain(mic, profile)
        self.notifier = Notifier(profile)

    def handleForever(self):
        """
        Delegates user input to the handling function when activated.
        """
        self._logger.info("Starting to handle conversation with keyword '%s'.",
                          self.persona)
        while True:
            # Print notifications until empty
            notifications = self.notifier.getAllNotifications()
            for notif in notifications:
                self._logger.info("Received notification: '%s'", str(notif))


            self._logger.debug("Started listening for keyword '%s'",
                               self.persona)

            print("conversation >> start listening for keyword %s" % self.persona)

            threshold, is_conversation_desired = self.mic.passiveListen(self.persona)
            self._logger.debug("Stopped listening for keyword '%s'",
                               self.persona)


            print("conversation >> stopped listening for keyword %s" % self.persona)

            if not is_conversation_desired:
                self._logger.info("Nothing has been said or transcribed.")
                print(">> Nothing has been said or transcribed.")
                continue
            self._logger.info("Keyword '%s' has been said!", self.persona)

            print("conversation >> Keyword %s has been said!" % self.persona)

            self._logger.debug("Started to listen actively with threshold: %r",
                               threshold)

            print("conversation >> Started to listen actively with threshold: %r" % threshold)

            input = self.mic.activeListenToAllOptions(threshold)
            self._logger.debug("Stopped to listen actively with threshold: %r",
                               threshold)

            print("conversation >> Stopped listening")

            if input:
                print("conversation >> recieved input: " + str(input))
                print("conversation >> Sending '{0}' to brain".format(input.get("_text")))
                self.brain.query(input.get("_text"))
            else:
                messages = ["You know, I can't help you if you mumble like that."
                            ,"Does not compute, how about we try this again."]

                message = random.choice(messages)

                self.mic.say(message)
