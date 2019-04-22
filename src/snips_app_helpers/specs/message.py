# coding=utf-8

import datetime
from collections import defaultdict
from string import Formatter
from textwrap import TextWrapper
import pathlib

from .. import utils


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


class Message(utils.BaseObj):
    STATIC_MSG = "NOT IMPLEMENTED"

    def __init__(self, **kwargs):
        self.__kwargs = sorted(kwargs.keys())
        for key, val in kwargs.items():
            setattr(self, key, val)

    @classmethod
    def _print_list_helper(cls, list_msg, message_list, helper_info=None):
        def kwargs_fn(msg):
            fieldnames = [
                fname for _, fname, _, _ in Formatter().parse(list_msg) if fname
            ]
            dic = dict()
            for fieldname in fieldnames:
                val = getattr(msg, fieldname)
                if isinstance(val, pathlib.Path):
                    val = val.name
                dic[fieldname] = val
            return dic

        final_msg = "%s:\n" % cls.STATIC_MSG

        final_msg += "\t%s" % (
            "\n\t".join(
                "- " + list_msg.format(**kwargs_fn(msg)) for msg in message_list
            )
        )
        if helper_info:
            wrapper = TextWrapper()
            wrapper.initial_indent = "\t\t"
            wrapper.subsequent_indent = "\t\t"
            final_msg += "\n\tRemarks:\n%s" % wrapper.fill(helper_info)

        return final_msg

    @staticmethod
    def print_list(message_list):
        raise NotImplementedError("please add it in your message subclass")

    @property
    def _signature(self):
        return "-".join(str(getattr(self, k)) for k in self.__kwargs)

    def __eq__(self, other):
        return self._signature == other._signature

    def __hash__(self):
        return hash(self._signature)

    def __str__(self):
        return "%s: %s" % (self.__class__.__name__, self.STATIC_MSG)


class System(Message):
    pass


class Info(Message):
    pass


class Warning(Message):
    pass


class Error(Message):
    pass


# dedicated Messages


class CorrectlyLinked(System):

    STATIC_MSG = "Correctly linked intent to action code"

    @classmethod
    def print_list(cls, message_list):
        return cls._print_list_helper(
            "@ {spec_filepath} applied to {action_dir} {intent_name}",
            message_list,
        )


class DetectedSpec(Info):

    STATIC_MSG = "Detected spec"

    @classmethod
    def print_list(cls, message_list):
        return cls._print_list_helper(
            "@ {spec_filepath} applied to {action_dir}", message_list
        )


class NoSpec(Warning):

    STATIC_MSG = "Missing spec for following actions"

    @classmethod
    def print_list(cls, message_list):
        return cls._print_list_helper("{action_dir}", message_list)


class IntentNotInAssistant(Warning):

    STATIC_MSG = "Action waiting intent not in assistant"

    @classmethod
    def print_list(cls, message_list):
        return cls._print_list_helper(
            "{intent_name} from action: {action_name}",
            message_list,
            helper_info="This should not be a problem except that it consume "
            "resource with useless purpose",
        )


class GenericCoveredIntent(Warning):

    STATIC_MSG = (
        "Intents do not seem to be covered with slot pattern by action code"
    )

    @classmethod
    def print_list(cls, message_list):
        return cls._print_list_helper(
            "@ {spec_filepath} applied to {action_dir} intent {intent_name}",
            message_list,
            helper_info="This limit the possible analysis.",
        )


class NotCoveredIntent(Error):

    STATIC_MSG = "Intents do not seem to be covered by any action code"

    @classmethod
    def print_list(cls, message_list):
        return cls._print_list_helper(
            "{intent_name}",
            message_list,
            helper_info="This might be due to missing spec in some action codes\n"
            "else you should take it seriously as no response at all will be given"
            " by your assistant to final user.",
        )


class IncoherentAssistantDatasetIntent(Error):

    STATIC_MSG = (
        "Intents do not seem to be in dataset.json but is in assistant.json"
    )

    @classmethod
    def print_list(cls, message_list):
        return cls._print_list_helper("{intent_name}", message_list)


class CoverageSlotSeq(Warning):

    STATIC_MSG = "Intents do not seem to cover the slot sequence"

    @classmethod
    def print_list(cls, message_list):
        return cls._print_list_helper(
            "@ {spec_filepath} intent {intent_name} {slots_utterances}",
            message_list,
        )


class MissingSlot(Error):

    STATIC_MSG = "Action code declared use of a slot NAME that does not exist in assistant"

    @classmethod
    def print_list(cls, message_list):
        return cls._print_list_helper(
            "@ {spec_filepath} intent {intent_name} slot_name {slot_name} not in {assistant_slot_names}",
            message_list,
        )


class InvalidSlotType(Error):

    STATIC_MSG = (
        "Action code declared use of a slot TYPE that is invalid in assistant"
    )

    @classmethod
    def print_list(cls, message_list):
        return cls._print_list_helper(
            "@ {spec_filepath} intent '{intent_name}' slot_name '{slot_name}' "
            "declared as type starting with '{slot_type}' but is '{expected_slot_type}' "
            "in assistant",
            message_list,
        )


class IntentHookedMultipleTimes(Warning):

    STATIC_MSG = "Some Intents seems to be hooked multiple times"

    @classmethod
    def print_list(cls, message_list):
        return cls._print_list_helper(
            "intent {intent_name} in actions: {action_names}",
            message_list,
            helper_info="While it might be legit do not forget that it means\n"
            "each time you trigger this intent n actions will be performed",
        )
