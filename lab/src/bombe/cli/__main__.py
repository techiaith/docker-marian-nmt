import click

from . import session, tasks

cli = click.Group(commands=dict(tasks=tasks.cli, session=session.cli))
cli()
