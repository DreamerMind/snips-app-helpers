# coding=utf-8
from __future__ import unicode_literals
from __future__ import print_function

import json
import datetime
from collections import defaultdict

from . import ActionSpec
from . import message


class IntentSpec(object):

    def __init__(self, name, id, slots, version):
        self.name = name
        self.id = id
        self.slots = slots
        self.version = version

    @classmethod
    def load(cls, dic_info):
        return IntentSpec(
            dic_info['name'],
            dic_info['id'],
            dic_info['slots'],
            dic_info['version'],
        )

    def __str__(self):
        return "<%s name=%s id=%s nb_slots=%s version=%s>" % (
            self.__class__.__name__,
            self.name,
            self.id,
            len(self.slots),
            self.version
        )

    def __repr__(self):
        return self.__str__()

    def __unicode__(self):
        return self.__str__()



class AssistantSpec(object):

    """ AssistantSpec Contract Specification """

    def __init__(self, name, language, versions, intents, created_at):
        self.name = name
        self.language = language
        self.versions = versions
        self._intents_list = intents
        self.created_at = created_at

    @property
    def intents(self):
        return {
            intent_spec.name: intent_spec
            for intent_spec in self._intents_list
        }

    @classmethod
    def load(cls, assistant_json):
        """ load specification from an assistant json file

        Args:
            assistant_json: pathlib.Path
        Return:
            AssistantSpec
        """
        with assistant_json.open(encoding='utf8') as fh:
            assistant_spec = json.load(fh)

        return AssistantSpec(
            name=assistant_spec['name'],
            created_at=assistant_spec['createdAt'],
            language=assistant_spec['language'],
            versions=assistant_spec.get('version', {}),
            intents=[
                IntentSpec.load(_) for _ in assistant_spec.get('intents', [])
            ],
        )

    def compare_to_action_specs(self, action_spec_list):
        report_msgs = []
        intents_coverage = defaultdict(list)
        for action_spec in action_spec_list:
            if not action_spec.have_spec:
                report_msgs.append(message.NoSpec(
                    'missing spec for %s' % action_spec.action_dir))
                continue
            for action_intent_trigger in action_spec.coverage:
                if action_intent_trigger in self.intents:
                    intents_coverage[action_intent_trigger].append(action_spec.name)
                else:
                    report_msgs.append(message.IntentNotInAssistant(
                        'Action waiting intent not in assistant: %s' % action_intent_trigger
                    ))
        for intent_name, action_names in intents_coverage.iteritems():
            if len(action_names) > 1:
                report_msgs.append(
                    message.IntentHookedMultipleTimes(
                        "Intent %s seems to be hooked multiple times in following action codes: %s" % (
                            intent_name, action_names
                        )
                    )
                )
        for not_covered_intent in set(self.intents).difference(intents_coverage):
            report_msgs.append(message.NotCoveredIntent(
                'Intent "%s" seems to not be covered by any action code !' % not_covered_intent
            ))
        return report_msgs

    def check(self, actions_dir):
        return self.compare_to_action_specs(
            ActionSpec.load_all_in_action_code_dir(actions_dir)
        )

    def __str__(self):
        return "<%s name='%s' lang='%s' nb_intents=%s versions=[%s] created_at=%s>" % (
            self.__class__.__name__,
            self.name,
            self.language,
            len(self.intents),
            ",".join("%s=%s" % (k, v) for k, v in self.versions.iteritems()),
            str(
                datetime.datetime.strptime(
                    self.created_at, "%Y-%m-%dT%H:%M:%S.%fZ").date())
        )

    def __repr__(self):
        return self.__str__()

    def __unicode__(self):
        return self.__str__()
