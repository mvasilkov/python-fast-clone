from contextlib import contextmanager
from datetime import datetime, timedelta
import hashlib
import os
import os.path
from pathlib import Path
import platform
import subprocess
from tempfile import TemporaryDirectory

from oslo_concurrency import lockutils

__all__ = ['fastclone']

CACHE = Path.home() / '.cache' / 'python-fast-clone'

CACHE_EXPIRE = timedelta(days=1)

CLEAN = 'nothing to commit, working tree clean'  # 2.14.1
CLEAN2 = 'nothing to commit, working directory clean'  # 2.7.4

LOCK_PATH = str(CACHE)

MSDOS = platform.system() == 'Windows'


def fastclone(repo: str, path: str, *, branch: str = None):
    sha224 = hashlib.sha224(repo.encode('utf-8')).hexdigest()
    lock = f'fastclone.{sha224}.lock'
    tarball = CACHE / f'{sha224}.tar'

    try:
        CACHE.mkdir(parents=True)
    except FileExistsError:
        pass

    @lockutils.synchronized(lock, external=True, lock_path=LOCK_PATH)
    def has_repo_cached() -> bool:
        try:
            updated = datetime.fromtimestamp(tarball.stat().st_mtime)
            return datetime.now() - updated < CACHE_EXPIRE
        except FileNotFoundError:
            return False

    @lockutils.synchronized(lock, external=True, lock_path=LOCK_PATH)
    def add_repo_to_cache():
        with TemporaryDirectory('.fastclone') as dirname:
            os.chdir(dirname)
            _clone(repo)
            _check_clean()
            _tar_c(tarball)
            if MSDOS:
                _unset_readonly()

    @lockutils.synchronized(lock, external=True, lock_path=LOCK_PATH)
    def unpack_repo():
        _tar_x(tarball, path)

    if not has_repo_cached():
        with dont_change_directory():
            try:
                add_repo_to_cache()
            except PermissionError:
                if not MSDOS:  # TemporaryDirectory.cleanup() forgot how to Windows
                    raise

    try:
        os.makedirs(path)
    except FileExistsError:
        pass

    unpack_repo()

    _pull(path, branch)


@contextmanager
def dont_change_directory():
    a = os.getcwd()
    try:
        yield
    finally:
        os.chdir(a)


def _run(args):
    return subprocess.run(
        [str(a) for a in args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        encoding='utf-8')


def _clone(repo: str):
    _run(['git', 'clone', '-q', repo, 'FOO'])


def _check_clean():
    p = _run(['git', '-C', 'FOO', 'status'])
    if CLEAN not in p.stdout and CLEAN2 not in p.stdout:
        raise RuntimeError('fastclone: Working tree not clean')


def _pull(path: str, branch: str = None):
    if branch is None:
        _run(['git', '-C', path, 'pull', '-q'])
    else:
        _run(['git', '-C', path, 'fetch', '-q'])
        _run(['git', '-C', path, 'checkout', '-q', branch])


def _relpath(a):
    return Path(os.path.relpath(a)).as_posix()


def _tar_c(tarball: Path):
    if MSDOS:
        tarball = _relpath(tarball)
    _run(['tar', 'cf', tarball, 'FOO'])


def _tar_x(tarball: Path, path: str):
    if MSDOS:
        tarball = _relpath(tarball)
        path = _relpath(path)
    _run(['tar', 'xf', tarball, '-C', path, '--strip-components', 1])


def _unset_readonly():
    _run(['attrib', '-R', 'FOO/*', '/S'])
