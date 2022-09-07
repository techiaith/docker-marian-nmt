from operator import attrgetter
import json

import click

from .. import training, sentences
from .utils import echo, training_session, experiment_dir_option


def _session_created_to_str(ts):
    created_at = ts.created.strftime('%d/%m/%Y %H:%M:%S')
    return '{} UTC'.format(created_at)


def _get_ts(ctx, training_session_id=None):
    if training_session_id:
        ts = training.Session.load(training_session_id)
    else:
        ts = ctx.obj
    return training_session(ts)


@click.group()
@click.pass_context
def cli(ctx):
    ctx.obj = training.Session.get()


@cli.command()
@click.option('-c', '--comment')
@click.option('--langs', default='en-cy')
@click.option('--classified-label', default='Health')
@click.option('--unclassified-label', default='Unknown')
@click.option('--hunspell-dir', type=click.Path(), default='/dictionaries')
@click.option('--data-dir', type=click.Path(), default='data/src')
@experiment_dir_option('config')
@experiment_dir_option('export')
@experiment_dir_option('logs')
@experiment_dir_option('models')
@experiment_dir_option('results')
@experiment_dir_option('spelling')
@experiment_dir_option('work')
@click.pass_context
def new(ctx, comment, **params):
    langs = params['langs']
    ts = training.Session.new(langs, comment=comment)
    params['export_columns'] = sentences.Translation._fields
    ts.settings.update(params)
    ts.save()
    ctx.obj = ts
    echo(str(ts))


@cli.command('list')
@click.option('-a', '--show-all', is_flag=True, default=False)
@click.option('-n', '--n-entries', type=int, default=10)
@click.pass_context
def list_sessions(ctx, show_all, n_entries):
    sessions = training.Session.registry()
    current = sessions.pop('current', None)
    line_pattern = '{0} {1} | Created: {2} | {3}'
    n = 0 if show_all else n_entries
    vals = list(sessions.values())[-n:]
    echo(f'Showing most recent {len(vals)} sessions.')
    for ts in reversed(sorted(vals, key=attrgetter('created'))):
        marker = '*' if ts == current else '-'
        comment = ts.comment or '<No comment provided>'
        echo(line_pattern.format(marker,
                                 ts,
                                 _session_created_to_str(ts),
                                 comment))


@cli.command()
@click.argument('training_session_id')
@click.option('-f', '--force', is_flag=True)
@click.option('-c', '--comment')
@click.option('--langs', default='en-cy')
@click.option('--classified-label', default='Health')
@click.option('--unclassified-label', default='Unknown')
@click.option('--hunspell-dir', type=click.Path(), default='/dictionaries')
@click.option('--data-dir', '/data/bombe')
@experiment_dir_option('config')
@experiment_dir_option('logs')
@experiment_dir_option('models')
@experiment_dir_option('results')
@experiment_dir_option('work')
@experiment_dir_option('export', 'data/export')
@experiment_dir_option('spelling')
@click.pass_context
def use(ctx, training_session_id, force, **params):
    ts = _get_ts(ctx, training_session_id)
    if force or ts is None:
        (langs, ident) = training_session_id.split('_')
        ts = training.Session(langs, ident, comment=params.get('comment'))
        params['export_columns'] = sentences.Translation._fields
        ts.settings.update(params)
        ts.save()
        ts = ts.load(training_session_id)
    if ts is None:
        echo(f'Training session {training_session_id} not found')


@cli.command()
@click.pass_context
def get(ctx):
    ts = training_session(ctx.obj)
    echo(str(ts))


@cli.command()
@click.pass_context
def end(ctx):
    ts = training_session(ctx.obj)
    ts.end()
    echo('Training session {} ended'.format(ts))


@cli.command()
@click.argument('comment')
@click.option('-s', '--training-session-id')
@click.pass_context
def annotate(ctx, comment, training_session_id):
    ts = _get_ts(ctx, training_session_id)
    ts.comment = comment
    ts.save()


@cli.command()
@click.option('-s', '--training_session_id', type=str)
@click.option('-k', '--split-number', type=int, default=1)
@click.pass_context
def duration(ctx, training_session_id, split_number):
    ts = _get_ts(ctx, training_session_id)
    log_path = ts.kfold_split_path('logs', split_number, 'marian.log')
    echo('{:0.2f} hours'.format(training.duration(log_path)))


@cli.command()
@click.argument('training_session_id')
@click.option('--full', is_flag=True, default=False)
def results(training_session_id, full):
    ts = training_session(training.Session.load(training_session_id))
    results = ts.get_results(training_session_id, summarize=not full)
    echo(json.dumps(results, default=str))


@cli.command()
@click.option('-s', '--training-session_id')
@click.pass_context
def scores(ctx, training_session_id):
    ts = _get_ts(ctx, training_session_id)
    summary = {}
    for k in ts.results:
        k_scores = ts.results[k]['scores']
        for (m, d) in k_scores.items():
            k = f'{k}'.zfill(2)
            summary.setdefault(f'split_{k}', {}).update({m: d['score']})
    echo(json.dumps(summary, sort_keys=True))


@cli.command()
@click.option('-s', '--training-session-id')
@click.pass_context
def view(ctx, training_session_id):
    ts = _get_ts(ctx, training_session_id)
    last_split_trained = ts.get_progress()
    settings = dict(ts.settings,
                    comment=ts.comment,
                    created=_session_created_to_str(ts),
                    last_split_trained=last_split_trained)
    padlen = max(map(len, settings))
    echo(f'Session: {ts}')
    echo('-' * padlen * 4)
    for (k, v) in sorted(settings.items()):
        if k in ts.folders and k.startswith(('models', 'logs')):
            v = ts.kfold_split_path(v.parts[-1], last_split_trained)
        if isinstance(v, (tuple, list)):
            v = ', '.join(v)
        echo(f'{k:{padlen}} {v}')


@cli.command()
@click.option('-s', '--training-session-id')
@click.pass_context
def rm(ctx, training_session_id):
    ts = _get_ts(ctx, training_session_id)
    ts.delete()


if __name__ == '__main__':
    cli()
