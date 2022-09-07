from pathlib import Path
from typing import Dict
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen, urlretrieve
import argparse
import json
import os
import subprocess as sp
import sys
import time


DOCKER_COMPOSE_TEMPLATE = """\
version: "3.7"

services:
  techiaith-marian-nmt:
    image: techiaith/docker-marian-nmt-api:{version}
    container_name: "{container_name}"
    environment:
      MARIAN_MODEL_NAME: "{marian_model_name}"
    volumes:
      - {base_dir}/server-models:/models
    entrypoint: ['python', '-m', 'uvicorn',
                 'bombe.translation.api.views:app',
                 '--host', '0.0.0.0',
                 '--port', '8000']
    ports:
      - "8000:8000"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              capabilities: [gpu]
volumes:
  server-models:
"""

GH_RELEASES_URL = 'https://api.github.com/repos/{repo}/releases'


def setup_directories(root: Path, model_name: str) -> Dict[str, Path]:
    root_dir = Path(root)
    root_dir.mkdir(parents=True, exist_ok=True)
    paths = {'config': root_dir / 'server-config',
             'logs': root_dir / 'server-logs',
             'models': root_dir / 'server-models' / model_name}
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def fetch_file(url, filename):
    try:
        print(f'Fetching {filename} ... ', end='', flush=True)
        retrieved = urlretrieve(url, filename=filename)
        print('done', flush=True)
    except HTTPError as err:
        print(f'Failed to fetch {filename} from {url}')
        raise err
    return retrieved[0]


def get_release(repo, tag):
    gh_url = GH_RELEASES_URL.format(repo=repo)
    if tag == 'latest':
        response = urlopen(gh_url + '/latest')
        return json.loads(response.read())
    response = urlopen(gh_url)
    releases = json.loads(response.read())
    it = (release
          for release in releases
          if release['tag_name'] == tag)
    return next(it)


def configure_docker_compose(repo, env_vars, dest_path):
    with open(dest_path, encoding='utf-8', mode='w') as dest_fp:
        content = DOCKER_COMPOSE_TEMPLATE.format(**env_vars)
        dest_fp.write(content)


def download_assets(release, dest):
    asset_urls = list(asset['browser_download_url']
                      for asset in release['assets'])
    assets = {}
    for asset_url in asset_urls:
        asset_name = Path(urlparse(asset_url).path).name
        path = fetch_file(asset_url, asset_name)
        assets[asset_name] = Path(path)
    return assets


def install_assets(assets, models_dir):
    for path in assets.values():
        target_path = models_dir / path.name
        if target_path.exists():
            continue
        renamed = path.rename(target_path)
        print('Installing asset: ', renamed)


def test_api():
    url = 'http://127.0.0.1:8000/api/translate'
    req = Request(url, method='HEAD')
    response = urlopen(req)
    if response.status != 200:
        print('Error: API Server failed to run!')
        print('\tStatus:', response.status)
        print('\tResponse:', response.read())
        print('Please type the following command to diagnose the error:')
        print('\tdocker compose logs')
    else:
        print(f'API server is up and running at {url}')


def run_cmd(cmd, from_dir, on_nonzero_exit_msg='', **kw):
    proc = sp.Popen(cmd,
                    cwd=from_dir,
                    shell=True,
                    stderr=sp.PIPE,
                    stdout=sp.PIPE,
                    **kw)
    piped = proc.communicate()
    (out, err) = tuple(stdx.decode('utf-8') for stdx in piped)
    if proc.returncode != 0 and on_nonzero_exit_msg:
        raise Exception(proc.returncode,
                        cmd,
                        on_nonzero_exit_msg)
    if out:
        print(out)
    if err:
        print(err)


def check_docker_compose_verison():
    run_cmd('docker compose version')


def run_marian_nmt(from_dir, container_name, model_name):
    run_cmd(f'docker compose up -d --remove-orphans {container_name}',
            from_dir,
            'Failed to start Marian NMT')


def stop_marian_nmt(from_dir, container_name):
    cmd = f'docker compose stop {container_name}'
    run_cmd(cmd, from_dir, 'Failed to run: {cmd}')


def marian_nmt_status(from_dir, container_name):
    cmd = f'docker compose ps {container_name}'
    run_cmd(cmd, from_dir)


if __name__ == '__main__':
    default_base_dir = os.getcwd()
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', default='techiaith/docker-marian-nmt')
    ap.add_argument('--release', default='latest')
    ap.add_argument('--base-dir', default=default_base_dir)
    ap.add_argument('--container-name', default='techiaith-marian-nmt')
    ap.add_argument('--model-name', default='iechyd-a-gofal')
    ap.add_argument('--install', action='store_true')
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--stop', action='store_true')
    ap.add_argument('--status', action='store_true')
    ns = ap.parse_args()
    base_dir = Path(ns.base_dir)
    dirs = setup_directories(base_dir, ns.model_name)
    release = get_release(ns.repo, ns.release)
    tag_name = release['tag_name']
    models_dir = dirs['models']
    compose_path = Path(base_dir, 'docker-compose.yml')
    if ns.install:
        assets = download_assets(release, models_dir)
        install_assets(assets, models_dir)
        if not compose_path.exists():
            env_vars = dict(version=tag_name,
                            marian_model_name=ns.model_name,
                            container_name=ns.container_name,
                            base_dir=base_dir)
            configure_docker_compose(ns.repo, env_vars, compose_path)
    uniopts = [ns.status, ns.stop, ns.run]
    if uniopts.count(True) > 1:
        print('Please use only one of --status, --stop, --run')
        sys.exit(1)
    if ns.status:
        marian_nmt_status(ns.base_dir, ns.container_name)
    elif ns.stop:
        stop_marian_nmt(ns.base_dir, ns.container_name)
    elif ns.run:
        run_marian_nmt(base_dir, ns.container_name, ns.model_name)
        time.sleep(1)
        test_api()
    else:
        if not ns.install:
            print('Please specify at least one option, see --help for more.')
            sys.exit(1)
