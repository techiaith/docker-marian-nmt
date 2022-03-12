from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, thishost, urlopen, urlretrieve
import argparse
import json
import os
import shlex
import subprocess as sp


GH_RELEASES_URL = 'https://api.github.com/repos/{repo}/releases'


def get_release(repo: str, tag: str):
    response = urlopen(GH_RELEASES_URL.format(repo=repo))
    releases = json.loads(response.read())
    if tag == 'latest':
        return releases[0]
    return next((release
                 for release in releases
                 if release['tag_name'] == tag), None)


def dowload_compose_file(repo: str, tag: str) -> Path:
    url = f'https://raw.githubusercontent.com/{repo}/{tag}'
    url += '/getting-started/docker-compose.yml'
    path = urlretrieve(url)[0]
    return Path(path)


def download_assets(release: str, asset_name, dest: Path):
    asset_urls = list(asset['browser_download_url']
                      for asset in release['assets'])
    assets = {}
    for asset_url in asset_urls:
        asset_name = Path(urlparse(asset_url).path).name
        path = urlretrieve(asset_url, filename=asset_name)[0]
        assets[asset_name] = path
    return assets


def install_assets(assets, models_dir):
    for path in assets.values():
        path.rename(models_dir, path.name)


def check_docker_compose_verison():
    proc = sp.Popen(shlex.split('docker compose version'),
                    stderr=sp.PIPE,
                    stdout=sp.PIPE)
    (err, out) = proc.communicate()
    if proc.returncode != 0:
        raise Exception('Please enable docker compose in your docker settings')


def run_marian_nmt(model_name):
    check_docker_compose_verison()
    cmd = 'docker compose up -d --remove-orphans techiaith-marian-nmt'
    sp.run(shlex.split(cmd), env=dict(MARIAN_MODEL_NAME=model_name))


def stop_marian_nmt():
    check_docker_compose_verison()
    for subcmd in ('stop', 'rm'):
        cmd = f'docker compose {subcmd} techiaith-marian-nmt'
        sp.run(shlex.split(cmd))


def test_api():
    host = thishost()[-1]
    url = f'http://{host}:8000/api'
    req = Request(url, method='HEAD')
    response = urlopen(req)
    if response.status != 200:
        print('Error: API Server failed to run!')
        print('\tStatus:', response.status)
        print('\tResponse:', response.read())
    else:
        print(f'API server is up and running at {url}')


if __name__ == '__main__':
    default_base_dir = os.path.expanduser('~/techiaith-docker-marian-nnt')
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', default='techiaith/docker-marian-nmt')
    ap.add_argument('--release', default='latest')
    ap.add_argument('--base-dir', default=default_base_dir)
    ap.add_argument('--model-name', default='iechyd-a-gofal')
    ap.add_argument('--fetch-assets',
                    default=True,
                    action=argparse.BooleanOptionalAction)
    ap.add_argument('--run',
                    default=True,
                    action=argparse.BooleanOptionalAction)
    ap.add_argument('--stop',
                    default=False,
                    action=argparse.BooleanOptionalAction)
    ns = ap.parse_args()
    base_dir = Path(ns.base_dir)
    Path(base_dir, 'server-config').mkdir(exist_ok=True)
    Path(base_dir, 'server-logs').mkdir(exist_ok=True)
    release = get_release(ns.repo, ns.release)
    compose_path = Path(base_dir, 'docker-compose.yml')
    if not compose_path.exists():
        dowload_compose_file(ns.repo, ns.release).rename(compose_path.name)
    models_dir = Path(base_dir, 'server-models', ns.model_name)
    models_dir.mkdir(parents=True, exist_ok=True)
    if ns.fetch_assets:
        assets = download_assets(release, models_dir)
        install_assets(assets, models_dir)
    if ns.run:
        run_marian_nmt(ns.model_name)
    if ns.stop:
        stop_marian_nmt()
