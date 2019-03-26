
from click.testing import CliRunner

from snips_app_helpers.cli import main


def test_main():
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert  'spec\n' in result.output
    assert result.exit_code == 0


def test_spec_check():
    # TODO check "snips-app spec check ..."
    pass
