# coding=utf-8
from __future__ import unicode_literals
from __future__ import print_function

import yaml


class ActionSpec(object):

    ATTRS = [
        "name",
        "supported_snips_versions",
        "version",
        "coverage",
        "udpated_at"
    ]

    def __init__(self,
                 action_dir,
                 have_spec=False, **kwargs):
        self.action_dir = action_dir
        self.have_spec = have_spec
        for k, v in kwargs.iteritems():
            if k in self.ATTRS:
                setattr(self, k, v)

    @classmethod
    def load(cls, action_dir):
        spec_filepath = action_dir / "spec.yml"
        if not spec_filepath.is_file():
            return ActionSpec(
                str(action_dir),
                have_spec=False
            )
        with spec_filepath.open('r') as fh:
            action_spec_dic = yaml.load(fh, Loader=yaml.FullLoader)
        return ActionSpec(
            action_dir=action_dir,
            have_spec=True,
            **{
                attr: action_spec_dic.get(attr)
                for attr in cls.ATTRS
            }
        )

    @classmethod
    def load_all_in_action_code_dir(cls, actions_dir):
        return [
            ActionSpec.load(action_dir)
            for action_dir in actions_dir.iterdir()
            if action_dir.is_dir()
        ]

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
