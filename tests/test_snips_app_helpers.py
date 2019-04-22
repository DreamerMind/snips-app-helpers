import os
from click.testing import CliRunner
import pytest
from pathlib import Path
import tempfile
import shutil

from snips_app_helpers.cli import main
from snips_app_helpers.specs import action
from snips_app_helpers.specs import assistant
from snips_app_helpers.specs import message
from snips_app_helpers.snips.dataset import Dataset
from snips_app_helpers import utils


filedir = os.path.dirname(os.path.abspath(__file__)) + "/../fixtures"


def coverage_check(action_spec_path):
    ass = assistant.Assistant.load(
        Path(os.path.join(filedir, "./assistant_1/assistant.json"))
    )
    action_spec = action.ActionSpec.load(
        Path(os.path.join(filedir, "./%s" % action_spec_path))
    )
    return action.CoverageSpec.load_from_spec(
        action_spec.coverage.to_spec(), action_spec
    ).check(ass)


def assistant_check(actions_dirname):
    return assistant.AssistantSpec.load(
        Path(os.path.join(filedir, "./assistant_1/assistant.json"))
    ).check(Path(os.path.join(filedir, "./%s" % actions_dirname)))


@pytest.mark.parametrize(
    "quantifier,number,is_in",
    [
        ("+", 1, True),
        ("+", 0, False),
        ("+", -1, False),
        ("?", 0, True),
        ("?", 1, True),
        ("?", 100, False),
        ("*", 0, True),
        ("*", 1, True),
        ("*", 100, True),
        ("*", -1, False),
        ("{1,3}", 100, False),
        ("{1,3}", 1, True),
        ("{1,3}", 0, False),
        ("{1,3}", 3, True),
        ("1", 100, False),
        ("1", 1, True),
        ("5", 5, True),
        ("a", 1, False),
    ],
)
def test_quantifier_check(quantifier, number, is_in):
    quanti = action.Quantifier(quantifier)
    assert quanti.contains(number) == is_in
    assert quantifier in str(quanti)


@pytest.mark.parametrize(
    "slot_name,quantifier,c_slot_name,c_slot_qte,is_in",
    [
        ("a", "?", "a", 1, True),
        ("a", "?", "b", 1, False),
        ("a", "?", "b", 0, False),
        ("ca", "+", "ca", 1, True),
        ("ca", "+", "ca", 0, False),
    ],
)
def test_coverage_block(slot_name, quantifier, c_slot_name, c_slot_qte, is_in):
    assert (
        action.CoverageRuleBlock.load_from_spec(slot_name, quantifier).cover(
            c_slot_name, c_slot_qte
        )
        == is_in
    )


@pytest.mark.parametrize(
    "rules_blocks,slot_occurences,is_in",
    [
        ([("a", "+"), ("b", "?")], [("a", 1), ("b", 1)], True),
        ([("a", "+"), ("b", "?")], [("a", 1), ("b", 2)], False),
        ([("a", "+"), ("b", "?")], [("a", 1)], True),
    ],
)
def test_coverage_rule(rules_blocks, slot_occurences, is_in):
    assert (
        action.CoverageRule.load_from_spec(rules_blocks).cover(slot_occurences)
        == is_in
    )


def test_exec_coverage_intent_spec():
    dataset = Dataset.from_json(
        "en", Path(os.path.join(filedir, "./assistant_1/dataset.json"))
    )
    ds_intent = dataset.intents[0]
    assert isinstance(
        action.CoverageIntentSpec.load_from_spec(
            ds_intent.name, [[("a", "+"), ("b", "?")]]
        ).check(ds_intent, action_spec_filepath="bloadsa"),
        set,
    )


def test_exec_coverage_spec():
    report_msgs, intents_coverage = coverage_check(
        action_spec_path="actions_1/Likhitha.Today/spec.yml"
    )
    assert isinstance(report_msgs, set)
    assert isinstance(intents_coverage, dict)


def test_check_detected_spec():
    assistant_spec = assistant.Assistant.load(
        Path(os.path.join(filedir, "./assistant_1/assistant.json"))
    )

    fp = Path(os.path.join(filedir, "./actions_1/Likhitha.Today/spec.yml"))
    report_msgs, intents_coverage = action.ActionSpec.load(fp).check(
        assistant_spec
    )

    assert isinstance(report_msgs, set)
    assert isinstance(intents_coverage, dict)
    detected_spec = next(
        report_msg
        for report_msg in report_msgs
        if isinstance(report_msg, message.DetectedSpec)
    )
    assert detected_spec.spec_filepath == fp.relative_to(fp.parent.parent)


def test_check_no_spec():
    assistant_spec = assistant.Assistant.load(
        Path(os.path.join(filedir, "./assistant_1/assistant.json"))
    )

    action_dirname = "Likhitha.Today"
    fp = Path(
        os.path.join(filedir, "./actions_1/%s/fake_spec.yml" % action_dirname)
    )
    report_msgs, intents_coverage = action.ActionSpec.load(fp).check(
        assistant_spec
    )

    assert isinstance(report_msgs, set)
    assert isinstance(intents_coverage, dict)
    no_spec = next(
        report_msg
        for report_msg in report_msgs
        if isinstance(report_msg, message.NoSpec)
    )
    assert no_spec.action_dir.name == action_dirname


def test_check_intent_nin_assistant():
    report_msgs, intents_coverage = coverage_check(
        action_spec_path="actions_1/Marshall.Music_Player/spec.yml"
    )
    assert any(
        (
            isinstance(report_msg, message.IntentNotInAssistant)
            and report_msg.intent_name == "MySuperFakeIntent"
        )
        for report_msg in report_msgs
    )


def test_check_not_covered_intent():
    report_msgs = assistant_check("actions_1")
    assert all(
        any(
            isinstance(report_msg, message.NotCoveredIntent)
            and report_msg.intent_name == intent_name
            for report_msg in report_msgs
        )
        for intent_name in [
            "getRandomTime",
            "bye",
            "shiftDown",
            "turnOff",
            "temperatureConverter",
            "getInfos",
            "day",
            "timeNow",
            "date",
            "setColor",
            "currencyConverter",
            "hello",
            "lengthConverter",
            "speedConverter",
            "setBrightness",
            "turnOn",
            "areaFunction",
            "getRandomDate",
            "previousSong",
            "setScene",
            "weightConverter",
            "speakerInterrupt",
        ]
    )


def test_check_coherent_assistant_dataset_intent():
    assert not any(
        isinstance(report_msg, message.IncoherentAssistantDatasetIntent)
        for report_msg in assistant_check("actions_1")
    )


def test_check_missing_slot():
    assert any(
        (
            isinstance(report_msg, message.MissingSlot)
            and report_msg.slot_name == "numberx"
        )
        for report_msg in assistant_check("actions_1")
    )


def test_intent_hooked_multiple_times():
    assert any(
        (
            isinstance(report_msg, message.IntentHookedMultipleTimes)
            and report_msg.intent_name == "getCurrentTime"
            and set(report_msg.action_names)
            == set(["Today", "Calculation", "Music Player"])
        )
        for report_msg in assistant_check("actions_1")
    )


def test_check_coverage_slot_seq():
    assert any(
        (
            isinstance(report_msg, message.CoverageSlotSeq)
            and report_msg.intent_name == "volumeConverter"
        )
        for report_msg in assistant_check("actions_1")
    )


def test_check_invalid_slot_type():
    assert any(
        (
            isinstance(report_msg, message.InvalidSlotType)
            and report_msg.slot_name == "percent"
        )
        for report_msg in assistant_check("actions_1")
    )


def test_check_correctly_linked():
    assert any(
        (
            isinstance(report_msg, message.CorrectlyLinked)
            and report_msg.intent_name == "playArtist"
        )
        for report_msg in assistant_check("actions_1")
    )


def test_check_generic_coverage():
    assert any(
        (
            isinstance(report_msg, message.GenericCoveredIntent)
            and report_msg.intent_name == "playPlaylist"
        )
        for report_msg in assistant_check("actions_1")
    )


@pytest.mark.parametrize(
    "quantities, quantifier",
    [
        ([0, 1], "?"),
        ([0, 2], "*"),
        ([0, 4, 2], "*"),
        ([1, 2, 5], "+"),
        ([0, 1, 2, 3, 4], "{0,4}"),
        ([2, 2, 2], "2"),
    ],
)
def test_quantifier_from_quantities(quantities, quantifier):
    assert (
        action.Quantifier.from_quantities(quantities)._quantifier == quantifier
    ), "quantities: %s" % str(quantities)


@pytest.mark.parametrize(
    "inp, out",
    [
        (  # sample 1
            set([frozenset(["a", "b"]), frozenset(["b", "c"])]),
            set(
                [
                    (frozenset(["a", "b"]), frozenset()),
                    (frozenset(["b", "c"]), frozenset()),
                ]
            ),
        ),
        (  # sample 2
            set(
                [
                    frozenset(["a", "b"]),
                    frozenset(["a"]),
                    frozenset(["b"]),
                    frozenset(["b", "c"]),
                ]
            ),
            set(
                [
                    (
                        frozenset(["a", "b"]),
                        frozenset([frozenset(["a"]), frozenset(["b"])]),
                    ),
                    (frozenset(["b", "c"]), frozenset()),
                ]
            ),
        ),
    ],
)
def test_group_set_subsets_of_others(inp, out):
    subsets = utils.group_set_subsets_of_others(inp)
    assert subsets == out


@pytest.mark.parametrize(
    "intent_name, rules_dic",
    [
        (
            "mathsQuestion",
            frozenset(
                [frozenset([("function", "{1,4}"), ("number", "{1,5}")])]
            ),
        ),
        ("playArtist", frozenset([frozenset([("artist_name", "1")])])),
    ],
)
def test_infer_slot_matching(intent_name, rules_dic):
    dataset = Dataset.from_json(
        "en", Path(os.path.join(filedir, "./assistant_1/dataset.json"))
    )
    intent_rules = action.CoverageIntentSpec.infer_from_dataset(
        intent_name, dataset
    )
    assert intent_rules.to_spec()[intent_name] == rules_dic


def test_autogenerate_spec():
    ass = assistant.AssistantSpec.load(
        Path(os.path.join(filedir, "./assistant_1/assistant.json"))
    ).assistant
    action_dirname = "Snips.Smart_Lights_-_Hue"
    action_dir = Path(os.path.join(filedir, "./actions_1/%s" % action_dirname))
    action_spec = action.ActionSpec.autoguess_spec(ass, action_dir)

    assert action_spec.name == "Snips Smart Lights - Hue"
    assert action_spec.slots == {
        "house_room": "entity",
        "percent": "snips/percentage",
        "color": "entity",
        "scene": "entity",
    }
    assert action_spec.coverage.to_spec() == {
        "date": frozenset(),  # TODO fix understand why
        "turnOn": frozenset({frozenset({("house_room", "{1,2}")})}),
        "turnOff": frozenset({frozenset({("house_room", "1")})}),
        "setBrightness": frozenset(
            {frozenset({("house_room", "{0,2}"), ("percent", "1")})}
        ),
        "setColor": frozenset(
            {frozenset({("color", "{1,2}"), ("house_room", "?")})}
        ),
        "setScene": frozenset(
            {frozenset({("scene", "1"), ("house_room", "?")})}
        ),
        "shiftUp": frozenset(
            {frozenset({("house_room", "?"), ("percent", "?")})}
        ),
        "shiftDown": frozenset(
            {frozenset({("house_room", "?"), ("percent", "?")})}
        ),
    }


def test_frozenset_to_list():
    res = utils.frozen_set_to_list({"a": frozenset(["a", "b"])})
    assert list(res.keys())[0] == "a"
    assert set(list(res.values())[0]) == set(["b", "a"])


def test_autogenerate_spec_save():
    ass = assistant.AssistantSpec.load(
        Path(os.path.join(filedir, "./assistant_1/assistant.json"))
    ).assistant
    action_dirname = "Snips.Smart_Lights_-_Hue"
    action_dir = Path(os.path.join(filedir, "./actions_1/%s" % action_dirname))
    action_spec = action.ActionSpec.autoguess_spec(ass, action_dir)
    with tempfile.NamedTemporaryFile() as fh:
        fp = Path(fh.name)
        action_spec.save(fp)
        assert fp.exists()


# Tests END to END


def test_main():
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert "spec\n" in result.output
    assert result.exit_code == 0


def test_main_with_param():
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--debug",
            "spec",
            "check",
            "-aj",
            os.path.join(filedir, "./assistant_1/assistant.json"),
            "--app_dir",
            os.path.join(filedir, "./actions_1/"),
        ],
    )
    assert "Detected spec:" in result.output
    assert result.exit_code == 0

    result = runner.invoke(
        main,
        [
            "spec",
            "check",
            "-aj",
            "./false_path",
            "--app_dir",
            os.path.join(filedir, "./actions_1/"),
        ],
    )
    assert "does not seems to be an existing file" in result.output
    assert result.exit_code == 0

    result = runner.invoke(
        main,
        [
            "spec",
            "check",
            "-aj",
            os.path.join(filedir, "./assistant_1/assistant.json"),
            "--app_dir",
            "falsepath",
        ],
    )
    assert "does not seems to be an existing folder" in result.output
    assert result.exit_code == 0


# E2E cli auto_guess
def test_cli_auto_guess():
    runner = CliRunner()
    specs_store = os.path.join(filedir, "./generated_specs")
    result = runner.invoke(
        main,
        [
            "--debug",
            "spec",
            "auto-guess",
            "-aj",
            os.path.join(filedir, "./assistant_1/assistant.json"),
            "--app_dir",
            os.path.join(filedir, "./actions_1/"),
            "-ss",
            specs_store,
        ],
    )
    assert result.exit_code == 0
    assert "Generated specs" in result.output
    shutil.rmtree(specs_store)
