# coding=utf-8

import json
import datetime
from collections import defaultdict

from . import ActionSpec
from . import message
from ..snips import Dataset
from ..snips import Assistant
from .. import utils


class AssistantSpec(utils.BaseObj):

    """ AssistantSpec

    Is here to allow to check all assistant specification against action codes
    """

    def __init__(self, assistant):
        self.assistant = assistant

    @classmethod
    def load(cls, filepath):
        return cls(Assistant.load(filepath))

    def compare_to_action_specs(self, action_spec_list):
        report_msgs = set()
        intents_coverage = defaultdict(list)
        for action_spec in action_spec_list:
            action_report_msgs, action_intents_coverage = action_spec.check(
                assistant=self.assistant
            )
            for cov_intent_name in action_intents_coverage:
                intents_coverage[cov_intent_name].append(action_spec.name)
            report_msgs.update(action_report_msgs)

        for intent_name, action_names in intents_coverage.items():
            if len(action_names) > 1:
                report_msgs.add(
                    message.IntentHookedMultipleTimes(
                        intent_name=intent_name, action_names=action_names
                    )
                )
        for not_covered_intent in set(self.assistant.intents).difference(intents_coverage):
            report_msgs.add(message.NotCoveredIntent(intent_name=not_covered_intent))
        return report_msgs

    def check(self, actions_dir):
        return self.compare_to_action_specs(
            ActionSpec.load_all_in_action_code_dir(actions_dir)
        )
