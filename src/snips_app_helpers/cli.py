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
@click.option('--debug/--no-debug', default=False)
def main(debug):
    if debug:
        click.echo('Debug mode is %s' % ('on' if debug else 'off'))


@main.group()
def spec():
    pass


@spec.command()
@click.option('-aj', '--assistant_json', required=True, type=pathlib.Path)
@click.option('-ad',
              '--app_dir',
              default=pathlib.Path('/var/lib/snips/skills'),
              type=pathlib.Path)
def check(assistant_json, app_dir):
    if not assistant_json.exists():
        click.echo(click.style('"%s" does not seems to be an existing file'
                               % str(assistant_json), fg='red'))
        return

    if not app_dir.exists():
        click.echo(click.style('"%s" does not seems to be an existing folder'
                               % str(app_dir), fg='red'))
        return
    click.echo(('Analysing spec for:\n'
                '\tassistant: %s\n'
                '\tapp dir: %s') % (str(assistant_json), app_dir))
    report_messages = specs.AssistantSpec.load(assistant_json).check(app_dir)
    SpecReportCli(report_messages).show()


class SpecReportCli(specs.message.Report):

    def show(self):
        for message in self.msgs:
            if isinstance(message, specs.message.Warning):
                click.echo(click.style(str(message), fg='yellow'))
            elif isinstance(message, specs.message.Error):
                click.echo(click.style(str(message), fg='red'))
