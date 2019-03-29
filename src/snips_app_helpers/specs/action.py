# coding=utf-8
from __future__ import unicode_literals
from __future__ import print_function

import yaml


class ActionSpec(object):

    FILENAME = "spec.yml"
    SUFFIX_EXTERAL_FILENAME = "." + FILENAME

    ATTRS = [
        "name",
        "supported_snips_versions",
        "version",
        "coverage",
        "udpated_at"
    ]

    def __init__(self,
                 spec_filepath,
                 action_dir,
                 have_spec=False, **kwargs):
        self.spec_filepath = spec_filepath
        self.action_dir = action_dir
        self.have_spec = have_spec
        for k, v in kwargs.iteritems():
            if k in self.ATTRS:
                setattr(self, k, v)

    @classmethod
    def load(cls, spec_filepath):
        if not spec_filepath.is_file():
            return ActionSpec(
                spec_filepath,
                spec_filepath.parent,
                have_spec=False
            )
        with spec_filepath.open('r') as fh:
            action_spec_dic = yaml.load(fh, Loader=yaml.FullLoader)

        if not action_spec_dic:
            raise ValueError("Spec %s is Empty !" % spec_filepath)

        action_dir = spec_filepath.parent
        if str(spec_filepath).endswith(cls.SUFFIX_EXTERAL_FILENAME):
            candidate_action_dir = action_dir.parent / spec_filepath.stem.replace('.spec', '')
            if candidate_action_dir.is_dir():
                action_dir = candidate_action_dir
            else:
                raise ValueError(
                    "A spec is defined that does not exists in any action"
                    "directory: not found dir %s" % candidate_action_dir
                )

        return ActionSpec(
            spec_filepath=spec_filepath,
            action_dir=action_dir,
            have_spec=True,
            **{
                attr: action_spec_dic.get(attr)
                for attr in cls.ATTRS
            }
        )

    @classmethod
    def load_all_in_action_code_dir(cls, actions_dir):
        actions_specs = []
        for action_dir in actions_dir.iterdir():
            if action_dir.is_dir():
                base_spec_filepath = action_dir / cls.FILENAME
                actions_specs.append(
                    ActionSpec.load(base_spec_filepath)
                )
                for another_spec in action_dir.glob('*.' + cls.FILENAME):
                    actions_specs.append(
                        ActionSpec.load(another_spec)
                    )
        return actions_specs

    def __str__(self):
        return "<%s action_dir='%s' %s>" % (
            self.__class__.__name__,
            self.action_dir,
            ("no-spec" if not self.have_spec else " ".join(
                "%s=%s" % (attr, getattr(self, attr)) for attr in self.ATTRS)
            )
        )

    def __repr__(self):
        return self.__str__()

    def __unicode__(self):
        return self.__str__()
