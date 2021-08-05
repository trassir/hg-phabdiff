from mercurial import extensions
from mercurial import commands
from .plugin import apply_phab_diff
from .logger import log


def _update_with_diff(orig, hgui, repo, *args, **kwargs):  # pragma: no cover
    orig_failed = orig(hgui, repo, *args, **kwargs)
    if orig_failed:
        return orig_failed
    repo_root = repo.url()
    if repo_root.startswith(b'file:'):
        repo_root = repo_root[5:]
    else:
        raise RuntimeError(
            'could not figure out repo location from "%s"' % repo_root)
    try:
        apply_phab_diff(repo_root.decode())
    except (RuntimeError, UnicodeDecodeError) as exc:
        log(exc, hgui)
        return True
    return False

def uisetup(_):  # pragma: no cover
    extensions.wrapcommand(commands.table, b'update', _update_with_diff)
