from pathlib import Path

from archgof.client import Client as ArchgofClient
from techiaith.utils.download import download_many_to

from .utils import fs


def _list_archgof_download_urls(domain_filter):
    urls = []
    client = ArchgofClient('https://cofion.techiaith.cymru', 'en')
    for item in client.list_all('api/submissions', set()):
        if domain_filter(item['domain']):
            filename = '{}.tmx'.format(item['id'])
            urls.append(client.format_url('submissions', filename))
    return urls


def _download_urls(data_dir, label, urls, show_progress_bar):
    path = Path(data_dir, label)
    fs.ensure_folders_exist(path)
    download_many_to(urls, path, progress_bar=show_progress_bar)


def _download_classified(data_dir, groups, show_progress_bar):
    domain_filter = lambda domain: domain == groups.classified  # noqa: E731
    urls = _list_archgof_download_urls(domain_filter)
    _download_urls(data_dir, groups.classified, urls, show_progress_bar)


def _download_unclassified(data_dir, groups, urls, show_progress_bar):
    domain_filter = lambda domain: domain != groups.classified  # noqa: E731
    urls = list(urls)
    urls.extend(_list_archgof_download_urls(domain_filter))
    _download_urls(data_dir, groups.unclassified, urls, show_progress_bar)


def download(data_dir, groups, urls, show_progress_bar=False):
    _download_unclassified(data_dir, groups, urls, show_progress_bar)
    _download_classified(data_dir, groups, show_progress_bar)
