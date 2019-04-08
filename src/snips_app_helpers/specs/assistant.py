# coding=utf-8
from __future__ import unicode_literals
from __future__ import print_function

import json
import datetime
from collections import defaultdict

from . import ActionSpec
from . import message
from ..dataset import Dataset
from .. import utils


class IntentSpec(utils.BaseObj):

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


class AssistantSpec(utils.BaseObj):

    """ AssistantSpec Contract Specification """

    def __init__(self, name, language, versions, intents, created_at, original_path):
        self.name = name
        self.language = language
        self.versions = versions
        self._intents_list = intents
        self.created_at = created_at
        self._original_path = original_path
        self._dataset = None

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
            original_path=assistant_json,
        )

    @property
    def dataset(self):
        if self._dataset:
            return self._dataset
        self._dataset = Dataset.from_json(
            self.language, self._original_path.parent / "dataset.json"
        )
        return self._dataset

    def _check_slots(self, action_intent_trigger, slot_spec, action_spec, spec_filepath):

        assistant_intent_slot_names, assistant_intent_slot_type = zip(*[
            (slot.get('name'), slot.get('entityId'))
            for slot in self.intents[action_intent_trigger].slots
        ])

        report_msgs = set()
        dataset_intent = self.dataset.intent_per_name.get(action_intent_trigger)
        if not dataset_intent:
            # incoherence between dataset.json and assistant.json !
            report_msgs.add(message.IncoherentAssistantDatasetIntent(
                spec_filepath=spec_filepath,

            ))
            return report_msgs
        else:
            # Check full coverage
            uncovered_seq = dataset_intent.slots_sequences.difference(
                [tuple(seq_case) for seq_case in slot_spec])
            for slot_seq in uncovered_seq:
                report_msgs.add(message.CoverageSlotSeq(
                    spec_filepath=spec_filepath,
                    intent_name=action_intent_trigger,
                    slots_sequences='[%s]' % ','.join(slot_seq)
                ))

        for intent_slot_config in slot_spec:
            for slot_name in intent_slot_config:
                try:
                    idx = assistant_intent_slot_names.index(slot_name)
                    if action_spec.slots:
                        slot_type = action_spec.slots.get(slot_name)
                        expected_slot_type = assistant_intent_slot_type[idx]
                        if slot_type and not expected_slot_type.startswith(slot_type):

                            report_msgs.add(message.InvalidSlotType(
                                spec_filepath=action_spec.spec_filepath.relative_to(
                                    action_spec.action_dir.parent
                                ),
                                intent_name=action_intent_trigger,
                                slot_name=slot_name,
                                slot_type=slot_type,
                                expected_slot_type=expected_slot_type,
                            ))
                except ValueError:
                    report_msgs.add(message.MissingSlot(
                        spec_filepath=action_spec.spec_filepath.relative_to(
                            action_spec.action_dir.parent
                        ),
                        intent_name=action_intent_trigger,
                        slot_name=slot_name,
                        assistant_slot_names=assistant_intent_slot_names,
                    ))
        return report_msgs

    def compare_to_action_specs(self, action_spec_list):
        report_msgs = set()
        intents_coverage = defaultdict(list)
        for action_spec in action_spec_list:
            spec_filepath = action_spec.spec_filepath.relative_to(
                action_spec.action_dir.parent
            )
            report_msgs.add(
                message.DetectedSpec(
                    spec_filepath=spec_filepath,
                    action_dir=action_spec.action_dir.name,
                )
            )
            if not action_spec.have_spec:
                report_msgs.add(message.NoSpec(
                    action_dir=action_spec.action_dir
                ))
                continue

            for action_intent_trigger, slot_spec in action_spec.coverage.items():
                if action_intent_trigger in self.intents:
                    if slot_spec:
                        report_msgs.update(self._check_slots(
                            action_intent_trigger,
                            slot_spec,
                            action_spec,
                            spec_filepath
                        ))
                    intents_coverage[action_intent_trigger].append(action_spec.name)
                else:
                    report_msgs.add(message.IntentNotInAssistant(
                        intent_name=action_intent_trigger,
                        action_name=action_spec.name,
                    ))
        for intent_name, action_names in intents_coverage.items():
            if len(action_names) > 1:
                report_msgs.add(
                    message.IntentHookedMultipleTimes(
                        intent_name=intent_name, action_names=action_names
                    )
                )
        for not_covered_intent in set(self.intents).difference(intents_coverage):
            report_msgs.add(message.NotCoveredIntent(intent_name=not_covered_intent))
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
            ",".join("%s=%s" % (k, v) for k, v in self.versions.items()),
            str(
                datetime.datetime.strptime(
                    self.created_at, "%Y-%m-%dT%H:%M:%S.%fZ").date())
        )
