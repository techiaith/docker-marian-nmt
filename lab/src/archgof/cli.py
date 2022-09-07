import json
from functools import partial

import click
from techiaith.utils.download import download_many_to
from dask.distributed import Client as DaskClient
try:
    from dask_cuda import LocalCUDACluster as DaskCluster
except ImportError:
    from dask.distributed import LocalCluster as DaskCluster


from .client import Client


SUBMISSIONS_ENDPOINT = 'api/submissions'


cli = click.Group()

option = partial(click.option, show_default=True)


@click.group()
@option('--service',
        default='https://cofion.techiaith.cymru')
@option('--lang', default='cy')
@click.pass_context
def cli(ctx, service, lang):
    ctx.obj = Client(service, lang)


@cli.command()
@option('--endpoint', '-e', default=SUBMISSIONS_ENDPOINT)
@option('--domain', '-d', multiple=True, default=())
@click.pass_context
def list_all(ctx, endpoint=None, domain=None):
    client = ctx.obj
    data = client.list_all(endpoint, domain)
    click.echo(json.dumps(data, indent=2))
    return data


@cli.command()
@option('--endpoint', default='submissions')
@option('--domain', '-d', multiple=True, default=())
@option('--data-dir',
        type=click.Path(),
        help='Directory to store downloaded TMX files.')
@click.pass_context
def download(ctx, endpoint, domain, data_dir):
    dl_client = ctx.obj
    cluster = DaskCluster()
    client = DaskClient(cluster)
    urls = []
    for info in dl_client.list_all(SUBMISSIONS_ENDPOINT, domain):
        filename = '{}.tmx'.format(info['id'])
        urls.append(dl_client.format_url(endpoint, filename))
    download_many_to(client, urls, data_dir)


if __name__ == '__main__':
    cli()
