#!/usr/bin/env python3
"""Build accepted Git-main source and run the agents control-plane dashboard on ASUS.

One image per revision (`agents-dashboard:<sha>`), one container on loopback 8765.
The dashboard reads the registries baked into its release (AGENTS_DASHBOARD_HOSTED=1),
so it shows exactly the published revision. Activation keeps the previous container
for rollback when the new one fails its health check.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import pwd
import re
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request

ROOT = Path('/srv/services/agents-dashboard')
CONTAINER = 'agents-dashboard'
PREVIOUS = 'agents-dashboard-previous'
LABEL = 'io.agents-dashboard.service'
REVISION_LABEL = 'org.opencontainers.image.revision'
DOCKER = ['docker', '--host', 'unix:///var/run/docker.sock']
PORT = 8765


class DeploymentError(Exception):
    def __init__(self, code, message, *, retryable=False):
        self.code, self.message, self.retryable = code, message, retryable
        super().__init__(message)


class MachineParser(argparse.ArgumentParser):
    def error(self, message):
        print(json.dumps({'status': 'error', 'error': {'code': 'E_ARGUMENT',
              'message': 'Invalid command arguments; see --help.', 'retryable': False}}))
        raise SystemExit(2)


def now():
    return datetime.now(timezone.utc).isoformat()


def execute(argv, *, cwd=None, timeout=30, check=True, output=None):
    env = {k: v for k, v in os.environ.items()
           if k not in {'DOCKER_HOST', 'DOCKER_CONTEXT', 'DOCKER_TLS_VERIFY', 'DOCKER_CERT_PATH'}}
    try:
        result = subprocess.run(argv, cwd=cwd, env=env, text=True, stdout=output or subprocess.PIPE,
                                stderr=output or subprocess.PIPE, timeout=timeout, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        raise DeploymentError('E_COMMAND', 'A bounded local deployment command failed; inspect deployment logs.') from exc
    if check and result.returncode:
        raise DeploymentError('E_COMMAND', 'A local deployment command returned an error; inspect deployment logs.')
    return result


def docker(*args, **kwargs):
    return execute([*DOCKER, *args], **kwargs)


def atomic_json(path, value):
    temporary = path.with_suffix('.tmp')
    with temporary.open('w') as stream:
        os.chmod(temporary, 0o600)
        json.dump(value, stream, sort_keys=True)
        stream.write('\n')
    temporary.replace(path)


def load_state(root):
    path = root / 'state.json'
    if not path.exists():
        return {'current': None, 'previous': None}
    try:
        value = json.loads(path.read_text())
        for release in (value['current'], value['previous']):
            if release is not None and (not re.fullmatch('[0-9a-f]{40}', release.get('revision', '')) or
                                        not re.fullmatch('sha256:[0-9a-f]{64}', release.get('image_id', ''))):
                raise ValueError()
        return value
    except (ValueError, TypeError, KeyError, OSError) as exc:
        raise DeploymentError('E_STATE', 'Release state is invalid; inspect it before deployment.') from exc


def inspect_container(name):
    result = docker('container', 'inspect', '--format', '{{json .}}', name, check=False)
    if result.returncode:
        docker('info', '--format', '{{json .ServerVersion}}', timeout=10)
        return None
    return json.loads(result.stdout)


def owned(container, release=None):
    labels = container.get('Config', {}).get('Labels') or {}
    if labels.get(LABEL) != 'dashboard':
        raise DeploymentError('E_CONTAINER_IDENTITY', 'The named container is not the agents dashboard.')
    if release and (labels.get(REVISION_LABEL) != release['revision'] or container.get('Image') != release['image_id']):
        raise DeploymentError('E_CONTAINER_IDENTITY', 'Container image/revision does not match recorded release state.')


def healthy(revision):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(f'http://127.0.0.1:{PORT}/api/control-plane', timeout=10) as response:
            value = json.loads(response.read(8 * 1024 * 1024))
    except (OSError, ValueError, urllib.error.URLError):
        return False
    return isinstance(value, dict) and value.get('release_sha') == revision


def wait_healthy(release, timeout=90):
    deadline = time.monotonic() + timeout
    while True:
        container = inspect_container(CONTAINER)
        if container:
            owned(container, release)
            if container['State']['Running'] and healthy(release['revision']):
                return
        if time.monotonic() >= deadline:
            raise DeploymentError('E_HEALTH', 'The agents dashboard did not become healthy at the expected revision.')
        time.sleep(1)


def status(root, expected_revision=None):
    state = load_state(root)
    release = state['current']
    data = {'revision': release['revision'] if release else None, 'installed': bool(release),
            'previous_revision': (state['previous'] or {}).get('revision'),
            'activation_pending': (root / 'activation.json').exists(), 'healthy': False}
    container = inspect_container(CONTAINER)
    if not release or not container or data['activation_pending']:
        return data
    owned(container, release)
    data['running'] = container['State']['Running']
    data['healthy'] = bool(data['running'] and healthy(release['revision'])
                           and (expected_revision is None or expected_revision == release['revision']))
    return data


def verify_source(source, revision):
    if not revision or not re.fullmatch('[0-9a-f]{40}', revision):
        raise DeploymentError('E_REVISION', 'Deploy requires a full lowercase 40-character Git commit.')
    def git(*args):
        return execute(['git', *args], cwd=source).stdout.strip()
    if git('rev-parse', 'HEAD') != revision:
        raise DeploymentError('E_REVISION', 'The release worktree HEAD differs from the requested revision.')
    if git('status', '--porcelain', '--untracked-files=no'):
        raise DeploymentError('E_SOURCE_DIRTY', 'Tracked release source has changes; publish accepted source first.')
    if execute(['git', 'merge-base', '--is-ancestor', revision, 'refs/remotes/origin/main'], cwd=source, check=False).returncode:
        raise DeploymentError('E_UNPUBLISHED', 'The requested revision is not in the fetched published main history.')


def verify_runtime(root):
    if sys.platform != 'linux' or os.geteuid() != 1000 or pwd.getpwuid(os.geteuid()).pw_name != 'homeserver-asus':
        raise DeploymentError('E_HOST', 'Deployment runs as homeserver-asus (UID 1000) on native ASUS Linux.')
    if not root.is_dir():
        raise DeploymentError('E_DATA', f'Create {root} (owned by homeserver-asus) before deployment.')


@contextmanager
def deployment_lock(root):
    with (root / 'deployment.lock').open('a') as handle:
        os.chmod(handle.name, 0o600)
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise DeploymentError('E_BUSY', 'Another agents dashboard deployment owns the lock.', retryable=True) from exc
        yield


def build_image(source, root, revision):
    logs = root / 'logs'
    logs.mkdir(exist_ok=True, mode=0o700)
    with tempfile.TemporaryDirectory(prefix='build-', dir=root) as temporary:
        directory = Path(temporary)
        archive = directory / 'source.tar'
        execute(['git', 'archive', '--format=tar', '-o', str(archive), revision], cwd=source)
        context = directory / 'context'
        context.mkdir()
        with tarfile.open(archive) as bundle:
            bundle.extractall(context, filter='data')
        with (logs / f'{revision}.log').open('a') as output:
            os.chmod(output.name, 0o600)
            docker('build', '--file', str(context / 'dashboard-app' / 'Dockerfile'),
                   '--build-arg', f'RELEASE_REVISION={revision}', '--tag', f'agents-dashboard:{revision}',
                   str(context), timeout=1500, output=output)
    value = json.loads(docker('image', 'inspect', '--format', '{{json .}}', f'agents-dashboard:{revision}').stdout)
    labels = value.get('Config', {}).get('Labels') or {}
    if labels.get(REVISION_LABEL) != revision or labels.get(LABEL) != 'dashboard':
        raise DeploymentError('E_IMAGE_IDENTITY', 'Built image does not contain the exact release identity labels.')
    return {'revision': revision, 'image_id': value['Id']}


def run_container(release):
    docker('run', '--detach', '--name', CONTAINER, '--restart', 'unless-stopped', '--user', '1000:1000',
           '--network', 'host', '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
           '--memory', '256m', '--tmpfs', '/tmp:rw,noexec,nosuid,size=32m', '--env', 'HOME=/tmp',
           '--log-opt', 'max-size=10m', '--log-opt', 'max-file=3', release['image_id'], timeout=30)


def activate(root, release, state):
    old = state['current']
    marker = root / 'activation.json'
    atomic_json(marker, {'started_at': now(), 'candidate': release, 'previous': old})
    current, previous = inspect_container(CONTAINER), inspect_container(PREVIOUS)
    try:
        if previous:
            owned(previous)
            docker('rm', '--force', PREVIOUS)
        if current:
            owned(current, old)
            docker('stop', '--time', '20', CONTAINER, timeout=40)
            docker('rename', CONTAINER, PREVIOUS)
        run_container(release)
        wait_healthy(release)
        atomic_json(root / 'state.json', {'current': release, 'previous': old, 'deployed_at': now()})
        marker.unlink()
    except BaseException as exc:
        try:
            if inspect_container(CONTAINER):
                docker('rm', '--force', CONTAINER)
            if old and inspect_container(PREVIOUS):
                docker('rename', PREVIOUS, CONTAINER)
                docker('start', CONTAINER)
                wait_healthy(old)
            atomic_json(root / 'state.json', {'current': old, 'previous': None, 'rollback_at': now()})
            marker.unlink()
        except BaseException as rollback_exc:
            raise DeploymentError('E_ROLLBACK', 'Activation and rollback failed; activation.json preserves recovery identities.') from rollback_exc
        if isinstance(exc, DeploymentError):
            raise exc
        raise DeploymentError('E_INTERRUPTED', 'Deployment was interrupted; the previous release was restored.') from exc


def deploy(root, source, revision):
    verify_runtime(root)
    verify_source(source, revision)
    with deployment_lock(root):
        if (root / 'activation.json').exists():
            raise DeploymentError('E_INCOMPLETE', 'An interrupted activation requires inspection; read activation.json first.')
        state = load_state(root)
        if state['current'] and state['current']['revision'] == revision and status(root, revision)['healthy']:
            return {**status(root, revision), 'changed': False}
        release = build_image(source, root, revision)
        activate(root, release, state)
        return {**status(root, revision), 'changed': True}


def main(argv=None):
    parser = MachineParser(description=__doc__)
    parser.add_argument('action', choices=('deploy', 'status', 'logs'))
    parser.add_argument('--revision')
    parser.add_argument('--lines', type=int, default=80)
    parser.add_argument('--json', action='store_true', help='JSON output is the default.')
    parser.add_argument('--no-input', action='store_true', help='All operations are noninteractive.')
    args = parser.parse_args(argv)
    if not 1 <= args.lines <= 500:
        parser.error('--lines must be between 1 and 500')
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        if args.action == 'deploy':
            data = deploy(ROOT, Path(__file__).resolve().parents[1], args.revision)
        elif args.action == 'status':
            data = status(ROOT, args.revision)
        else:
            container = inspect_container(CONTAINER)
            if not container:
                raise DeploymentError('E_NOT_INSTALLED', 'No agents dashboard container is installed.')
            owned(container)
            result = docker('logs', '--tail', str(args.lines), CONTAINER, timeout=10)
            data = {'logs': ((result.stdout or '') + (result.stderr or ''))[-65536:]}
        print(json.dumps({'status': 'ok', 'data': data}, sort_keys=True))
        return 0
    except DeploymentError as exc:
        print(json.dumps({'status': 'error', 'error': {'code': exc.code, 'message': exc.message,
                                                       'retryable': exc.retryable}}, sort_keys=True))
        return 1
    except (Exception, KeyboardInterrupt):
        print(json.dumps({'status': 'error', 'error': {'code': 'E_RUNTIME',
                         'message': 'Local deployment state could not be inspected.', 'retryable': False}}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
