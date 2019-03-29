# coding=utf-8

from __future__ import unicode_literals
from __future__ import print_function

import datetime
from collections import defaultdict
from string import Formatter
from textwrap import TextWrapper


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
    STATIC_MSG = "NOT IMPLEMENTED"

    def __init__(self, **kwargs):
        for key, val in kwargs.iteritems():
            setattr(self, key, val)

    @classmethod
    def _print_list_helper(cls, list_msg, message_list, helper_info=None):
        def kwargs_fn(msg):
            fieldnames = [
                fname
                for _, fname, _, _ in Formatter().parse(list_msg)
                if fname]
            return {
                fieldname: getattr(msg, fieldname)
                for fieldname in fieldnames
            }
        final_msg = "%s:\n" % cls.STATIC_MSG

        final_msg += '\t%s' % ("\n\t".join(
            "- " + list_msg.format(**kwargs_fn(msg)) for msg in message_list
        ))
        if helper_info:
            wrapper = TextWrapper()
            wrapper.initial_indent = "\t\t"
            wrapper.subsequent_indent = "\t\t"
            final_msg += '\n\tRemarks:\n%s' % wrapper.fill(helper_info)

        return final_msg

    @staticmethod
    def print_list(message_list):
        raise NotImplementedError("please add it in your message subclass")


    def __str__(self):
        return "%s: %s" % (self.__class__.__name__, self.STATIC_MSG)

    def __repr__(self):
        return self.__str__()

    def __unicode__(self):
        return self.__str__()


class Info(Message):
    pass


class Warning(Message):
    pass


class Error(Message):
    pass

# dedicated Messages


class DetectedSpec(Info):

    STATIC_MSG = 'Detected spec'

    @classmethod
    def print_list(cls, message_list):
        return cls._print_list_helper(
            "@ {spec_filepath} applied to {action_dir}", message_list)


class NoSpec(Warning):

    STATIC_MSG = 'Missing spec for following actions'

    @classmethod
    def print_list(cls, message_list):
        return cls._print_list_helper("{action_dir}", message_list)


class IntentNotInAssistant(Warning):

    STATIC_MSG = 'Action waiting intent not in assistant'

    @classmethod
    def print_list(cls, message_list):
        return cls._print_list_helper(
            "{intent_name} from action: {action_name}",
            message_list,
            helper_info="This should not be a problem except that it consume "
            "resource with useless purpose"
        )


class NotCoveredIntent(Error):

    STATIC_MSG = 'Intents do not seem to be covered by any action code'

    @classmethod
    def print_list(cls, message_list):
        return cls._print_list_helper(
            "{intent_name}",
            message_list,
            helper_info="This might be due to missing spec in some action codes\n"
            "else you should take it seriously as no response at all will be given"
            " by your assistant to final user.",
        )


class IntentHookedMultipleTimes(Warning):

    STATIC_MSG = 'Some Intents seems to be hooked multiple times'

    @classmethod
    def print_list(cls, message_list):
        return cls._print_list_helper(
            "intent {intent_name} in actions: {action_names}",
            message_list,
            helper_info="While it might be legit do not forget that it means\n"
            "each time you trigger this intent n actions will be performed"
        )
