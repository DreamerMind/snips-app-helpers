# coding=utf-8
from __future__ import unicode_literals
from __future__ import print_function

import datetime
from collections import defaultdict


class Report(object):

    def __init__(self, msgs):
        self.created_at = datetime.datetime.now()
        self.msgs = msgs

    @property
    def grouped_messages(self):
        grp = defaultdict(list)
        for msg in self.msgs:
            grp[msg.__class__].append(msg)
        return grp


# base messages

class Message(object):
    def __init__(self, **kwargs):
        for key, val in kwargs.iteritems():
            setattr(self, key, val)

    @property
    def msg(self):
        raise NotImplementedError("please add it in your message subclass")

    @staticmethod
    def print_list(message_list):
        raise NotImplementedError("please add it in your message subclass")


    def __str__(self):
        return "%s: %s" % (self.__class__.__name__, self.msg)

    def __repr__(self):
        return self.__str__()

    def __unicode__(self):
        return self.__str__()


class Warning(Message):
    pass


class Error(Message):
    pass

# dedicated Messages


class NoSpec(Warning):

    @property
    def msg(self):
        return 'missing spec for %s' % self.action_dir

    @staticmethod
    def print_list(message_list):
        return 'Missing spec for following actions:\n\t%s' % "\n\t".join(
            "- %s" % msg.action_dir for msg in message_list
        )


class IntentNotInAssistant(Warning):

    @property
    def msg(self):
        return 'Action waiting intent not in assistant:\n\t%s' % self.intent_name

    @staticmethod
    def print_list(message_list):
        return 'Action waiting intent not in assistant:\n\t%s' % "\n\t".join(
            "- %s" % msg.intent_name for msg in message_list
        )


class NotCoveredIntent(Error):

    @property
    def msg(self):
        return 'Intent "%s" seems to not be covered by any action code !' % self.intent_name

    @staticmethod
    def print_list(message_list):
        return 'Intents do not seem to be covered by any action code:\n\t%s' % "\n\t".join(
            "- %s" % msg.intent_name for msg in message_list
        )


class IntentHookedMultipleTimes(Warning):

    @property
    def msg(self):
        return "Intent %s seems to be hooked multiple times in following action codes:\n\t%s" % (
            self.intent_name, self.action_names
        )

    @staticmethod
    def print_list(message_list):
        return 'Some Itents seems to be hooked multiple times:\n\t%s' % "\n\t".join(
            "- intent %s in actions: %s" % (msg.intent_name, msg.action_names)for msg in message_list
        )
