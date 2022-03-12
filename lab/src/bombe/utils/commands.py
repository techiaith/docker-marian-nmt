from importlib import resources as ir
import shlex
import subprocess as sp

from .. import scripts


class CommandError(Exception):
    """Raised if a command failed."""


def run(cmd, **kw):
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    stdout = kw.pop('stdout', sp.PIPE)
    stderr = kw.pop('stderr', sp.PIPE)
    completed = sp.run(cmd, stdout=stdout, stderr=stderr, **kw)
    if completed.returncode != 0:
        raise CommandError(completed.stderr.decode('utf-8'),
                           ' '.join(cmd))
    if stdout is sp.PIPE:
        return completed.stdout.decode('utf-8').strip()
    return None


def run_script(script_name, *script_args, **sp_kw):
    with ir.path(scripts, script_name) as script:
        return run([script] + list(script_args), **sp_kw)
