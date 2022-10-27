from decimal import Decimal
from functools import partial
from itertools import repeat
from multiprocessing import Pool
from pathlib import Path
import shutil

import click
from more_itertools import flatten
import srsly
from tqdm import tqdm

from .. import downloading, marian_nmt, sentences, splitting, training
from ..spelling import SpellCheck
from ..utils import commands, fs
from .utils import echo, training_session


@click.group()
@click.pass_context
def cli(ctx, **options):
    ts = training.Session.get()
    ctx.obj = ts


@cli.command()
@click.argument('url', nargs=-1)
@click.pass_context
def download_data(ctx, url):
    ts = training_session(ctx.obj)
    params = dict(ts.settings)
    data_dir = params['data_dir']
    groups = splitting.GroupLabels(params['classified_label'],
                                   params['unclassified_label'])
    downloading.download(data_dir, groups, url, show_progress_bar=True)


@cli.command()
@click.option('-j', '--num-procs',
              help='Number of processes',
              default=4,
              type=int)
@click.pass_context
def export_and_clean(ctx, num_procs):
    ts = training_session(ctx.obj)
    params = ts.settings
    dict_dir = params['hunspell_dir']
    data_dir = params['data_dir']
    export_dir = params['export_dir']
    columns = params['export_columns']
    spelling_dir = params['spelling_dir']
    spell_checkers = {lang: SpellCheck(lang, dict_dir, spelling_dir)
                      for lang in ts.langs}
    clean = partial(sentences.clean,
                    ts.langs,
                    spell_checkers,
                    columns,
                    export_dir)
    source_paths = list(fs.DirectoryTree(data_dir))
    pbar = tqdm(total=len(source_paths), desc='Export and clean data')
    with Pool(processes=num_procs) as pool:
        with pbar:
            for _ in pool.imap_unordered(clean, source_paths):
                pbar.update()


@cli.command()
@click.pass_context
def split_corpus(ctx):
    ts = training_session(ctx.obj)
    params = ts.settings
    work_dir = params['work_dir']
    langs = ts.langs
    export_dir = params['export_dir']
    export_columns = params['export_columns']
    group_labels = splitting.GroupLabels(params['classified_label'],
                                         params['unclassified_label'])
    corpus = sentences.load(export_dir, export_columns)
    classifier_group = corpus.classifier
    (train_sets, test_set) = splitting.split(langs,
                                             corpus,
                                             classifier_group,
                                             group_labels,
                                             test_size=0.1,
                                             k_folds=10)
    splitting.save(train_sets, test_set, langs, work_dir)


def _save_results(langs, ts, split_n, scores, log_path, work_dir):
    labeled_dirs = dict((dirname.split('_')[0], path)
                        for (dirname, path) in ts.folders.items())
    file_sizes = dict((label, fs.file_sizes(dirname))
                      for (label, dirname) in labeled_dirs.items())
    seg_stats = fs.segment_stats(work_dir, langs)
    duration = '{:0.2f}'.format(Decimal(training.duration(log_path)))
    ts.results[split_n] = dict(scores=scores,
                               file_sizes=file_sizes,
                               segments=seg_stats,
                               duration=duration)
    ts.save()


@cli.command()
@click.pass_context
def train(ctx):
    ts = training_session(ctx.obj)
    params = ts.settings
    langs = ts.langs
    config_dir = params['config_dir']
    models_dir = params['models_dir']
    work_dir = params['work_dir']
    train_splits = splitting.paths(work_dir, langs, 'train')
    valid_splits = splitting.paths(work_dir, langs, 'valid')
    vocab_path = marian_nmt.get_vocab_path(langs, models_dir)
    config_path = Path(config_dir, 'transformers.yml')
    if not config_path.exists():
        marian_nmt.configure(langs, config_path, vocab_path)
    if not vocab_path.exists():
        train_paths = flatten(train_splits)
        marian_nmt.create_spm_vocab(config_path, vocab_path, train_paths)
    last_trained_split = ts.get_progress()
    splits = zip(train_splits, valid_splits)
    n_splits = len(train_splits)
    untrained = list(splits)[last_trained_split:]
    n_untrained = len(untrained)
    start = last_trained_split + 1
    pbar = tqdm(total=n_untrained,
                initial=start,
                mininterval=60. * 10,
                colour='green')
    for k, (train_sets, valid_sets) in enumerate(untrained, start=start):
        pbar.set_description(
            desc=f'Marian NMT model training - K-fold split {k}/{n_splits}')
        models_dir = ts.kfold_split_path('models', k)
        logs_dir = ts.kfold_split_path('logs', k)
        model = models_dir / 'model.npz'
        log = logs_dir / 'marian.log'
        valid_log = logs_dir / 'marian-validation.log'
        vt_out = models_dir / f'valid.{langs.target}.out'
        mdec_log = logs_dir / 'marian-decoder.log'
        marian_nmt.train(langs,
                         config_path,
                         model,
                         log,
                         valid_log,
                         vt_out,
                         train_sets,
                         valid_sets)
        ts.save_progress(k)
        scores = marian_nmt.score(langs,
                                  models_dir,
                                  work_dir,
                                  mdec_log,
                                  vt_out)
        echo(srsly.json_dumps({k: str(v) for (k, v) in scores.items()}))
        _save_results(langs, ts, k, scores, log, work_dir)
        pbar.update()
    if ts.get_progress() == n_splits:
        echo(f'Training finished for all {n_splits} splits')


@cli.command()
@click.argument('split-number', type=int)
@click.option('-s', '--training-session-id', default=None)
@click.option('--save-results', is_flag=True, default=False)
@click.pass_context
def score(ctx, split_number, training_session_id, save_results):
    if training_session_id:
        ts = training.Session.load(training_session_id)
    else:
        ts = ctx.obj
    params = dict(ts.settings)
    langs = ts.langs
    model_path = partial(ts.kfold_split_path, 'models', split_number)
    models_dir = model_path()
    work_dir = params['work_dir']
    log = ts.kfold_split_path('logs', split_number, 'marian-decoder.log')
    vt_out = model_path(f'valid.{langs.target}.out')
    scores = marian_nmt.score(langs, models_dir, work_dir, log, vt_out)
    if save_results:
        _save_results(langs, ts, split_number, scores, log, work_dir)
    scores_summary = {metric: d['score'] for (metric, d) in scores.items()}
    echo(srsly.json_dumps(scores_summary))


@cli.command()
@click.pass_context
def run_me(ctx):
    echo(commands.run_script('run-me.sh'))


@cli.command()
@click.argument('model_name')
@click.argument('config_models_dir', type=click.Path())
@click.argument('dest_dir_root', type=click.Path())
@click.pass_context
def publish_model(ctx, model_name, config_models_dir, dest_dir_root):
    ts = training_session(ctx.obj)
    dest_dir = Path(dest_dir_root, model_name)
    splits = list(ts.results)
    scores = list(ts.results[k]['scores']['BLEU']
                  for k in splits)
    best_score = max(scores)
    best_split = scores.index(best_score) + 1
    model_split_path = partial(ts.kfold_split_path, 'models', best_split)
    decoder_config_path = model_split_path(marian_nmt.DECODER_CONFIG_FILENAME)
    decoder_config = srsly.read_yaml(decoder_config_path)
    fs.ensure_folders_exist(dest_dir)
    model = Path(decoder_config['models'][0])
    vocab = Path(decoder_config['vocabs'][0])
    config_model_name = 'model.npz'
    shutil.copy(model, dest_dir / config_model_name)
    shutil.copy(vocab, dest_dir / vocab.name)
    config_models_dir = Path(config_models_dir, model_name)
    config_model = config_models_dir / config_model_name
    decoder_config['models'] = [str(config_model)]
    vocab_path = Path(config_models_dir) / vocab.name
    decoder_config['vocabs'] = list(map(str, repeat(vocab_path, 2)))
    decoder_config_name = f'{config_model_name}.decoder.yml'
    with open(dest_dir / decoder_config_name, 'w') as fp:
        fp.write(srsly.yaml_dumps(decoder_config))
    echo(f'Path: {fp.name}')


if __name__ == '__main__':
    cli()
