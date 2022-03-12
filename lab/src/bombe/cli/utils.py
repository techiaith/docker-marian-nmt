from functools import partial
from pathlib import Path
from pprint import pformat

import click


ExperimentDir = partial(click.Path,
                        resolve_path=True,
                        dir_okay=True,
                        file_okay=False)


def echo(msg, *args, **echo_opts):
    echo_opts.setdefault('color', True)
    nl = echo_opts.pop('nl', None) or not args
    msg = msg if isinstance(msg, str) else pformat(msg)
    click.echo(msg, nl=nl, **echo_opts)
    for arg in args:
        click.echo(pformat(arg), **echo_opts)


def training_session(ts):
    if ts is None:
        echo('No training session is active')
        echo('Use: bombe.cli session use <tsid>')
        raise click.Abort()
    return ts


def experiment_dir_option(name, subdir=None):
    subdir = subdir or name
    return click.option(
        f'--{name}-dir',
        type=ExperimentDir(),
        # partial format string : will be completed when training
        # session id available.
        default=Path('/experiments/{}' + f'/{subdir}'))
