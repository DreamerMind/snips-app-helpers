# coding=utf-8
from __future__ import unicode_literals
from __future__ import print_function

from . import AppSpec


class AssistantSpec(object):

    """ AssistantSpec Contract Specification """

    def __init__(self):
        pass

    @classmethod
    def load(cls, assistant_json):
        """ load specification from an assistant json file

        Args:
            assistant_json: pathlib.Path
        Return:
            AssistantSpec
        """
        pass

    def compare_to_app_specs(app_spec_list):
        pass

    def check(self, skill_dir):
        app_specs = AppSpec.load_all_in_skill_dir(skill_dir)
        return self.compare_to_app_specs(app_specs)
