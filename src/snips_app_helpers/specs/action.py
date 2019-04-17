# coding=utf-8

from collections import defaultdict

import yaml

from .. import utils
from . import message


class Quantifier(utils.BaseObj):

    def __init__(self, quantifier_str):
        self._quantifier = str(quantifier_str)

    def contains(self, quantity):
        if self._quantifier == '+':
            if quantity <= 0:
                return False
        elif self._quantifier == '*':
            if quantity < 0:
                return False
        elif self._quantifier == '?':
            if quantity < 0 or quantity > 1:
                return False
        elif self._quantifier.startswith('{') and self._quantifier.endswith('}'):
            # implement {1,10}
            start, end = map(int,
                             self._quantifier.replace('{', '').replace('}', '').split(','))
            if not (start <= quantity <= end):
                return False
        else:
            try:
                qte = int(self._quantifier)
                if quantity != qte:
                    return False
            except ValueError:
                return False
        return True

    def __str__(self):
        return "<%s %s>" % (
            self.__class__.__name__,
            self._quantifier,
        )


class CoverageRuleBlock(utils.BaseObj):

    def __init__(self, slot_name, quantifier):
        self.slot_name = slot_name
        self.quantifier = quantifier

    def cover(self, slot_name, slot_qte):
        return (
            slot_name == self.slot_name and self.quantifier.contains(slot_qte)
        )

    @classmethod
    def load_from_spec(cls, slot_name, quantifier_str):
        return cls(
            slot_name,
            quantifier=Quantifier(quantifier_str),
        )

    def __str__(self):
        return "<%s slot_name=%s quantifier=%s>" % (
            self.__class__.__name__,
            self.slot_name,
            self.quantifier,
        )


class CoverageRule(utils.BaseObj):

    def __init__(self, rule_blocks):
        self.rule_blocks = rule_blocks

    @classmethod
    def load_from_spec(cls, rule_blocks):
        return cls(
            list(CoverageRuleBlock.load_from_spec(slot_name, quantifier)
            for slot_name, quantifier in rule_blocks)
        )

    def cover(self, slot_occurences):
        if not slot_occurences:
            True

        # TODO fix: check that every pattern as been consumed
        # for all elm of sequence
        return all(
            # at least one coverage block match the elm
            any(
                rule_block.cover(slot_name, slot_qte)
                for rule_block in self.rule_blocks
            )
            for slot_name, slot_qte in slot_occurences
        )

    def __str__(self):
        return "<%s rules=%s>" % (
            self.__class__.__name__,
            self.rule_blocks
        )


class CoverageIntentSpec(utils.BaseObj):

    def __init__(self, intent_name, rules):
        self.name = intent_name
        self.rules = rules

    @classmethod
    def load_from_spec(cls, intent_name, intent_cov_spec):
        return cls(intent_name, [
            CoverageRule.load_from_spec(rule_sequence)
            for rule_sequence in intent_cov_spec
        ])

    def covered_slots_sequence(self, slots_sequences):
        # iter over coverage rules and check it is a valid
        covered_slot_seq = set()
        for slots_sequence in slots_sequences:
            for rule in self.rules:
                if rule.cover(slots_sequence):
                    covered_slot_seq.add(slots_sequence)
                    break
        return covered_slot_seq

    def uncovered_slots_sequence(self, slots_sequences):
        return set(tuple(seq_case) for seq_case in slots_sequences).difference(
            self.covered_slots_sequence(slots_sequences))

    def check(self, dataset_intent, action_spec_filepath):
        report_msgs = set()
        # Check full coverage
        uncovered_seq = self.uncovered_slots_sequence(dataset_intent.slots_sequences)
        for slot_seq in uncovered_seq:
            report_msgs.add(message.CoverageSlotSeq(
                spec_filepath=action_spec_filepath,
                intent_name=self.name,
                slots_sequences='[%s]' % ', '.join(
                    "%dx %s" % (qte, sn) for sn, qte in slot_seq
                )
            ))
        return report_msgs

    def __str__(self):
        return "<%s rules=%s>" % (
            self.__class__.__name__,
            self.rules
        )


class CoverageSpec(utils.BaseObj):

    def __init__(self, intents_specs, action_spec=None):
        self.intents = intents_specs
        self._action_spec = action_spec

    def set_linked_action_spec(self, action_spec):
        self._action_spec = action_spec

    @property
    def action_spec(self):
        if self._action_spec is None:
            raise ValueError(
                "call to action_spec before setting it with "
                "set_linked_action_spec or at init time."
            )
        return self._action_spec

    @classmethod
    def load_from_spec(cls, spec_coverage_dic, action_spec=None):
        return CoverageSpec(
            {
                intent_name: CoverageIntentSpec.load_from_spec(
                    intent_name,
                    intent_cov_spec
                ) if intent_cov_spec else None
                for intent_name, intent_cov_spec in spec_coverage_dic.items()
            },
            action_spec=action_spec
        )

    def check_slot_consistancy(self, assistant_intent):
        report_msgs = set()

        if not assistant_intent.slots:
            assistant_intent_slot_names, assistant_intent_slot_type = [], []
        else:
            assistant_intent_slot_names, assistant_intent_slot_type = zip(*[
                (slot.get('name'), slot.get('entityId'))
                for slot in assistant_intent.slots
            ])

        for intent_name, intent_slot_config in self.intents.items():
            if intent_name not in assistant_intent.name:
                continue
            if not intent_slot_config:
                continue
            for rule in intent_slot_config.rules:
                for rule_block in rule.rule_blocks:
                    slot_name = rule_block.slot_name
                    try:
                        idx = list(assistant_intent_slot_names).index(slot_name)
                        if self.action_spec.slots:
                            slot_type = self.action_spec.slots.get(slot_name)
                            expected_slot_type = list(assistant_intent_slot_type)[idx]
                            if slot_type and not expected_slot_type.startswith(slot_type):
                                report_msgs.add(message.InvalidSlotType(
                                    spec_filepath=self.action_spec.rel_filepath,
                                    intent_name=intent_name,
                                    slot_name=slot_name,
                                    slot_type=slot_type,
                                    expected_slot_type=expected_slot_type,
                                ))
                    except ValueError:
                        report_msgs.add(message.MissingSlot(
                            spec_filepath=self.action_spec.rel_filepath,
                            intent_name=intent_name,
                            slot_name=slot_name,
                            assistant_slot_names=assistant_intent_slot_names,
                        ))
        return report_msgs

    def check(self, assistant):
        # intents_coverage, dataset
        report_msgs = set()
        intents_coverage = defaultdict(list)
        for action_intent_name, slot_spec in self.intents.items():
            if action_intent_name in assistant.intents:
                if slot_spec:
                    dataset_intent = assistant.dataset.intent_per_name.get(
                        action_intent_name
                    )
                    if dataset_intent:
                        intent_messages = set()
                        intent_messages.update(slot_spec.check(
                            dataset_intent=dataset_intent,
                            action_spec_filepath=self.action_spec.rel_filepath
                        ))
                        intent_messages.update(
                            self.check_slot_consistancy(
                                assistant.intents[action_intent_name]
                            )
                        )
                        if not intent_messages:
                            intent_messages.add(
                                message.CorrectlyLinked(
                                    spec_filepath=self.action_spec.rel_filepath,
                                    action_dir=self.action_spec.action_dir,
                                    intent_name=action_intent_name
                                )
                            )
                        report_msgs.update(intent_messages)
                    else:
                        # incoherence between dataset.json and assistant.json !
                        report_msgs.add(message.IncoherentAssistantDatasetIntent(
                            spec_filepath=self.action_spec.rel_filepath,

                        ))
                else:
                    report_msgs.add(
                        message.GenericCoveredIntent(
                            spec_filepath=self.action_spec.rel_filepath,
                            action_dir=self.action_spec.action_dir.name,
                            intent_name=action_intent_name
                        )
                    )
                intents_coverage[action_intent_name].append(self.action_spec.name)
            else:
                report_msgs.add(message.IntentNotInAssistant(
                    intent_name=action_intent_name,
                    action_name=self.action_spec.name,
                ))

        return (report_msgs, intents_coverage)

    def __str__(self):
        return "<%s cover_rules=%s>" % (
            self.__class__.__name__,
            self.intents,
        )


class ActionSpec(utils.BaseObj):

    FILENAME = "spec.yml"
    SUFFIX_EXTERAL_FILENAME = "." + FILENAME

    ATTRS = [
        "name",
        "supported_snips_versions",
        "version",
        "coverage",
        "_coverage_dic",
        "slots",
        "udpated_at"
    ]

    def __init__(self,
                 filepath,
                 action_dir,
                 have_spec=False, **kwargs):
        self.filepath = filepath
        self.action_dir = action_dir
        self.have_spec = have_spec
        for k, v in kwargs.items():
            if k in self.ATTRS:
                setattr(self, k, v)

    @property
    def rel_filepath(self):
        return self.filepath.relative_to(self.action_dir.parent)

    @classmethod
    def load(cls, filepath):
        if not filepath.is_file():
            return ActionSpec(
                filepath,
                filepath.parent,
                have_spec=False
            )
        with filepath.open('r') as fh:
            action_spec_dic = yaml.load(fh, Loader=yaml.FullLoader)

        if not action_spec_dic:
            raise ValueError("Spec %s is Empty !" % filepath)

        action_dir = filepath.parent
        if str(filepath).endswith(cls.SUFFIX_EXTERAL_FILENAME):
            candidate_action_dir = action_dir.parent / filepath.stem.replace('.spec', '')
            if candidate_action_dir.is_dir():
                action_dir = candidate_action_dir
            else:
                raise ValueError(
                    "A spec is defined that does not exists in any action"
                    "directory: not found dir %s" % candidate_action_dir
                )

        kwargs = {
            attr: action_spec_dic.get(attr)
            for attr in cls.ATTRS
        }
        kwargs["_coverage_dic"] = kwargs["coverage"]
        kwargs["coverage"] = CoverageSpec.load_from_spec(kwargs["coverage"])

        action_spec = ActionSpec(
            filepath=filepath,
            action_dir=action_dir,
            have_spec=True,
            **kwargs
        )
        kwargs["coverage"].set_linked_action_spec(action_spec)
        return action_spec

    @classmethod
    def load_all_in_action_code_dir(cls, actions_dir):
        actions_specs = []
        for action_dir in actions_dir.iterdir():
            if action_dir.is_dir():
                base_filepath = action_dir / cls.FILENAME
                actions_specs.append(
                    ActionSpec.load(base_filepath)
                )
                for another_spec in action_dir.glob('*.' + cls.FILENAME):
                    actions_specs.append(
                        ActionSpec.load(another_spec)
                    )
        return actions_specs

    def check(self, assistant):
        report_msgs = set()
        report_msgs.add(
            message.DetectedSpec(
                spec_filepath=self.rel_filepath,
                action_dir=self.action_dir.name,
            )
        )
        if not self.have_spec:
            report_msgs.add(message.NoSpec(
                action_dir=self.action_dir.name
            ))
            return (report_msgs, {})

        cov_msgs, intents_coverage = self.coverage.check(assistant)
        report_msgs.update(cov_msgs)
        return (report_msgs, intents_coverage)

    def __str__(self):
        return "<%s action_dir='%s' %s>" % (
            self.__class__.__name__,
            self.action_dir,
            ("no-spec" if not self.have_spec else " ".join(
                "%s=%s" % (attr, getattr(self, attr)) for attr in self.ATTRS)
            )
        )
