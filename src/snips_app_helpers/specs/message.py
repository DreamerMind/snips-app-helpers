# coding=utf-8
from __future__ import unicode_literals
from __future__ import print_function

import datetime


class Report(object):

    def __init__(self, msgs):
        self.created_at = datetime.datetime.now()
        self.msgs = msgs


# base messages

class Message(object):
    def __init__(self, msg):
        self.msg = msg

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
    pass


class IntentNotInAssistant(Warning):
    pass


class NotCoveredIntent(Error):
    pass


class IntentHookedMultipleTimes(Warning):
    pass
