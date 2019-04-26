# coding=utf-8

import json
import datetime

from . import Dataset
from .. import utils


class AssistantIntent(utils.BaseObj):
    def __init__(self, name, id, slots, version):
        self.name = name
        self.id = id
        self.slots = slots
        self.version = version

    @classmethod
    def load(cls, dic_info):
        return AssistantIntent(
            dic_info["name"],
            dic_info["id"],
            dic_info["slots"],
            dic_info["version"],
        )

    def __str__(self):
        return "<%s name=%s id=%s nb_slots=%s version=%s>" % (
            self.__class__.__name__,
            self.name,
            self.id,
            len(self.slots),
            self.version,
        )


class Assistant(utils.BaseObj):

    """ Assistant Specification """

    def __init__(
        self,
        name,
        language,
        versions,
        intents,
        created_at,
        original_path,
        platform,
        asr,
        hotword,
        analytics_enabled,
        heartbeat_enabled,
    ):
        self.name = name
        self.language = language
        self.versions = versions
        self._intents_list = intents
        self.created_at = created_at
        self._original_path = original_path
        self._dataset = None
        self.platform = platform
        self.asr = asr
        self.hotword = hotword
        self.analytics_enabled = analytics_enabled
        self.heartbeat_enabled = heartbeat_enabled

    @property
    def intents(self):
        return {
            intent_spec.name: intent_spec for intent_spec in self._intents_list
        }

    @classmethod
    def load(cls, assistant_json):
        """ load specification from an assistant json file

        Args:
            assistant_json: pathlib.Path
        Return:
            Assistant
        """
        with assistant_json.open(encoding="utf8") as fh:
            assistant_spec = json.load(fh)

        return Assistant(
            name=assistant_spec["name"],
            created_at=assistant_spec["createdAt"],
            language=assistant_spec["language"],
            versions=assistant_spec.get("version", {}),
            intents=[
                AssistantIntent.load(_)
                for _ in assistant_spec.get("intents", [])
            ],
            original_path=assistant_json,
            platform=assistant_spec["platform"]["type"],
            asr=assistant_spec["asr"]["type"],
            hotword=assistant_spec["hotword"],
            analytics_enabled=assistant_spec["analyticsEnabled"],
            heartbeat_enabled=assistant_spec["heartbeatEnabled"],
        )

    @property
    def dataset(self):
        if self._dataset:
            return self._dataset
        self._dataset = Dataset.from_json(
            self.language, self._original_path.parent / "dataset.json"
        )
        return self._dataset

    def __str__(self):
        return (
            "<%s name='%s' lang='%s' nb_intents=%s versions=[%s] created_at=%s>"
            % (
                self.__class__.__name__,
                self.name,
                self.language,
                len(self.intents),
                ",".join("%s=%s" % (k, v) for k, v in self.versions.items()),
                str(
                    datetime.datetime.strptime(
                        self.created_at, "%Y-%m-%dT%H:%M:%S.%fZ"
                    ).date()
                ),
            )
        )
