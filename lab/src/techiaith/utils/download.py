"""Utlities for downloading data."""
from collections import namedtuple
from functools import partial
from pathlib import Path
from urllib.parse import urlparse
from typing import Dict, Generator, Optional, Sequence, Union
from multiprocessing.pool import Pool
import contextlib
import logging
import os
import gzip
import lzma
import zlib

from tqdm import tqdm
import requests


log = logging.getLogger(__name__)


DownloadSpec = namedtuple(
    'DownloadSpec',
    ('url', 'storage_path', 'compression_type'))
"""
    A download_spec is a three-tuple of:
    1. url
    2. Local storage path.
    3. Compression type (may be None).
"""

decompressors = dict(xz=lzma.decompress,
                     gz=gzip.decompress,
                     zip=zlib.decompress)
"""Supported decompression schemes."""


class DownloadError(Exception):
    """Raised when a download error occurred."""


def get_download_spec(
        url: str,
        data_dir: Union[Path, str]) -> DownloadSpec:
    """Return a `DownloadSpec` for a given `url`."""
    parsed = urlparse(url)
    comp_types = set(decompressors)
    if parsed.path.endswith(tuple(f'.{dc}' for dc in comp_types)):
        comp_type = os.path.splitext(parsed.path)[-1][1:]
    else:
        comp_type = None
    filename_parts = Path(parsed.path).parts[1:]
    filename = Path('_'.join(filename_parts))
    if comp_type is not None:
        filename = filename.with_suffix('')
    storage_path = Path(data_dir, filename)
    return DownloadSpec(url, storage_path, comp_type)


def download(
        url: str,
        chunk_size: int = 8192) -> Generator[str, None, None]:
    """A generator that downloads data from `url` in chunks.

    Optionally provide a `chunk_size`.

    Yields successive chunks until all data is downloaded.
    """
    response = requests.get(url, stream=True)
    if not response.ok:
        raise DownloadError(f'Failed to download: {url}',
                            dict(status=response.status,
                                 text=response.content))
    with response:
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=None):
            yield chunk


def download_to(
        download_spec: [Union[DownloadSpec, tuple]],
        overwrite_existing: Optional[bool] = False) -> None:
    """Download data for a given `download_spec`.

    See also: `DownloadSpec`.
    """
    path = download_spec.storage_path
    path.parent.mkdir(parents=True,
                      exist_ok=True)
    with open(download_spec.storage_path, 'wb') as fp:
        for chunk in download(download_spec.url):
            log.debug(download_spec)
            decompress = decompressors.get(download_spec.compression_type)
            if decompress is not None:
                data = decompress(chunk)
            else:
                data = chunk
            fp.write(data)


def download_many_to(
        urls: Sequence[Union[Path, str]],
        data_dir: Path,
        overwrite_existing: Optional[bool] = False,
        progress_bar: Optional[bool] = False,
) -> Dict[str, DownloadSpec]:
    """Download a sequence of `urls` to local directory `data_dir`.

    Returns a mapping of path to `DownloadSpec` tuples.
    """
    dl_specs = []
    for url in urls:
        dl_spec = get_download_spec(url, data_dir)
        dl_specs.append(dl_spec)
    download_url_to = partial(download_to,
                              overwrite_existing=overwrite_existing)
    with Pool(processes=4) as pool:
        if progress_bar:
            pbar = tqdm(total=len(dl_specs))
        else:
            pbar = contextlib.suppress()
        with pbar:
            for dl in pool.imap_unordered(download_url_to, dl_specs):
                if progress_bar:
                    pbar.update()


__all__ = ('download',
           'download_to',
           'download_many_to',
           'get_download_spec',
           'DownloadSpec',
           'decompressors')
