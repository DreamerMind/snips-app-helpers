"""
Module that contains the command line app.

Why does this file exist, and why not put this in __main__?

  You might be tempted to import things from __main__ later, but that will cause
  problems: the code will get executed twice:

  - When you run `python -msnips_app_helpers` python will execute
    ``__main__.py`` as a script. That means there won't be any
    ``snips_app_helpers.__main__`` in ``sys.modules``.
  - When you import __main__ it will get executed again (as a module) because
    there's no ``snips_app_helpers.__main__`` in ``sys.modules``.

  Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""
import pathlib

import click

from . import specs


@click.group()
@click.option("--debug/--no-debug", default=False)
def main(debug):
    if debug:
        click.echo("Debug mode is %s" % ("on" if debug else "off"))


@main.group()
def spec():
    pass


@spec.command()
@click.option(
    "-aj",
    "--assistant_json",
    default=pathlib.Path("/usr/share/snips/assistant/assistant.json"),
    type=pathlib.Path,
)
@click.option(
    "-ad",
    "--app_dir",
    default=pathlib.Path("/var/lib/snips/skills"),
    type=pathlib.Path,
)
def check(assistant_json, app_dir):
    if not assistant_json.exists():
        click.echo(
            click.style(
                '"%s" does not seems to be an existing file'
                % str(assistant_json),
                fg="red",
            )
        )
        return

    if not app_dir.exists():
        click.echo(
            click.style(
                '"%s" does not seems to be an existing folder' % str(app_dir),
                fg="red",
            )
        )
        return
    click.echo(
        ("Analysing spec for:\n" "\tassistant: %s\n" "\tapp dir: %s")
        % (
            click.style(str(assistant_json), fg="cyan"),
            click.style(str(app_dir), fg="cyan"),
        )
    )
    report_messages = specs.AssistantSpec.load(assistant_json).check(app_dir)
    SpecReportCli(report_messages).show()


@spec.command()
@click.option(
    "-aj",
    "--assistant_json",
    default=pathlib.Path("/usr/share/snips/assistant/assistant.json"),
    type=pathlib.Path,
)
@click.option(
    "-ad",
    "--app_dir",
    default=pathlib.Path("/var/lib/snips/skills"),
    type=pathlib.Path,
)
@click.option("-ss", "--spec_store", type=pathlib.Path)
def auto_guess(assistant_json, app_dir, spec_store):
    if not assistant_json.exists():
        click.echo(
            click.style(
                '"%s" does not seems to be an existing file'
                % str(assistant_json),
                fg="red",
            )
        )
        return

    if not app_dir.exists():
        click.echo(
            click.style(
                '"%s" does not seems to be an existing folder' % str(app_dir),
                fg="red",
            )
        )
        return

    if not spec_store.exists():
        spec_store.mkdir(parents=True)
    click.echo("Generate guessed spec in %s" % spec_store)
    spec_assistant = specs.AssistantSpec.load(assistant_json)
    action_names = set()
    for msg in spec_assistant.check(app_dir):
        if isinstance(msg, specs.message.NoSpec):
            action_spec = specs.ActionSpec.autoguess_spec(
                spec_assistant.assistant, msg.action_dir
            )
            action_spec.save(spec_store / (msg.action_dir.name + ".spec.yml"))
            action_names.add(msg.action_dir.name)
    click.echo(
        "Generated specs (%s) in %s" % (",".join(action_names), spec_store)
    )


class SpecReportCli(specs.message.Report):
    def _print_list(self, msg_type, messages, color):
        click.echo(
            click.style(str("\n" + msg_type.print_list(messages)), fg=color)
        )

    def show(self):
        # infos on top
        for msg_type, messages in self.grouped_messages.items():
            if issubclass(msg_type, specs.message.Info):
                self._print_list(msg_type, messages, "cyan")

        for msg_type, messages in self.grouped_messages.items():
            if issubclass(msg_type, specs.message.Warning):
                self._print_list(msg_type, messages, "yellow")
            elif issubclass(msg_type, specs.message.Error):
                self._print_list(msg_type, messages, "red")
