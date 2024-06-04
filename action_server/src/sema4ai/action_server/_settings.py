import logging
import os
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterator, Optional

from termcolor import colored

from sema4ai.action_server.vendored_deps.termcolors import bold_red

from ._protocols import ArgumentsNamespaceMigrateImportOrStart

log = logging.getLogger(__name__)


def is_frozen():
    if getattr(sys, "frozen", False):
        return True
    try:
        __file__
    except NameError:
        return True

    return False


def get_python_exe_from_env(env):
    python = env.get("PYTHON_EXE")
    if not python:
        if is_frozen():
            raise RuntimeError(
                "Unable to run because no 'action-server.yaml' was present to bootstrap the environment\n"
                "(note: when the action server is distributed without sources, an 'action-server.yaml' for "
                "the target environment is always required)."
            )
        else:
            python = sys.executable

    return python


def _old_get_default_settings_dir() -> Path:
    if sys.platform == "win32":
        localappdata = os.environ.get("LOCALAPPDATA")
        if not localappdata:
            raise RuntimeError("Error. LOCALAPPDATA not defined in environment!")
        path = Path(localappdata) / "robocorp" / ".action_server"
    else:
        # Linux/Mac
        path = Path("~/robocorp/.action_server").expanduser()
    return path


@lru_cache
def get_default_settings_dir() -> Path:
    home_env_var = os.environ.get("SEMA4AI_HOME")
    if home_env_var:
        home = Path(home_env_var)
    else:
        if sys.platform == "win32":
            localappdata = os.environ.get("LOCALAPPDATA")
            if not localappdata:
                raise RuntimeError("Error. LOCALAPPDATA not defined in environment!")
            home = Path(localappdata) / "sema4ai"
        else:
            # Linux/Mac
            home = Path("~/.sema4ai").expanduser()

    default_settings_dir = home / "action-server"

    # Notify users about backward incompatible change
    # (as this is lru-cached, should notify only once).
    old_dir = _old_get_default_settings_dir()
    if os.path.exists(old_dir):
        log.critical(
            bold_red(
                f"""Note: the action server settings are now stored in:
{default_settings_dir}

instead of:
{old_dir}

If you want to keep data on old runs, consider moving
the contents of {old_dir} to {default_settings_dir}

-- otherwise, please remove:
{old_dir}

so that this message is no longer shown.
"""
            )
        )

    default_settings_dir.mkdir(parents=True, exist_ok=True)
    return default_settings_dir


@lru_cache
def get_user_sema4_path() -> Path:
    if sys.platform == "win32":
        localappdata = os.environ.get("LOCALAPPDATA")
        if not localappdata:
            raise RuntimeError("Error. LOCALAPPDATA not defined in environment!")
        home = Path(localappdata) / "sema4ai"
    else:
        # Linux/Mac
        home = Path("~/.sema4ai").expanduser()

    user_sema4_path = home / "action-server"
    user_sema4_path.mkdir(parents=True, exist_ok=True)
    return user_sema4_path


@dataclass(slots=True, kw_only=True)
class Settings:
    artifacts_dir: Path
    datadir: Path

    title: str = "Sema4.ai Action Server"

    address: str = "localhost"
    port: int = 8080
    verbose: bool = False
    db_file: str = "server.db"
    expose_url: str = "sema4ai.link"
    server_url: str = "http://localhost:8080"

    min_processes: int = 2
    max_processes: int = 20
    reuse_processes: bool = False

    full_openapi_spec: bool = False

    @classmethod
    def defaults(cls):
        fields = cls.__dataclass_fields__
        ret = {}
        SENTINEL = []
        for name, field in fields.items():
            v = getattr(field, "default", SENTINEL)
            if v is not SENTINEL:
                ret[name] = v
        return ret

    @classmethod
    def _create(cls, args: ArgumentsNamespaceMigrateImportOrStart) -> "Settings":
        user_specified_datadir = args.datadir
        if not user_specified_datadir:
            import hashlib

            curr_cwd_dir = Path(".").absolute()
            name = curr_cwd_dir.name
            as_posix = curr_cwd_dir.as_posix()
            if sys.platform == "win32":
                as_posix = as_posix.lower()

            # Not secure, but ok for our purposes
            short_hash = hashlib.sha256(as_posix.encode()).hexdigest()[:8]
            datadir_name = f"{get_default_settings_dir()}/{name}_{short_hash}"

            log.info(colored(f"Using datadir: {datadir_name}", attrs=["dark"]))
            user_expanded_datadir = Path(datadir_name).expanduser()

        else:
            log.info(f"Using user-specified datadir: {user_specified_datadir}")
            user_expanded_datadir = Path(user_specified_datadir).expanduser()

        datadir = user_expanded_datadir.absolute()

        settings = Settings(datadir=datadir, artifacts_dir=datadir / "artifacts")
        # Optional (just in 'start' command, not in 'import')
        for attr in (
            "address",
            "port",
            "min_processes",
            "max_processes",
            "reuse_processes",
            "full_openapi_spec",
        ):
            assert hasattr(settings, attr)
            if hasattr(args, attr):
                setattr(settings, attr, getattr(args, attr))

        if hasattr(args, "server_url") and args.server_url is not None:
            settings.server_url = args.server_url
        else:
            settings.server_url = f"http://{settings.address}:{settings.port}"

        # Used in either import or start commands.
        settings.verbose = args.verbose
        settings.db_file = args.db_file
        return settings

    def to_uvicorn(self):
        return {
            "host": self.address,
            "port": self.port,
            "reload": False,
            "log_config": None,
        }


_global_settings: Optional[Settings] = None


@contextmanager
def setup_settings(
    args: ArgumentsNamespaceMigrateImportOrStart,
) -> Iterator[Settings]:
    global _global_settings
    settings = Settings._create(args)
    _global_settings = settings
    try:
        yield settings
    finally:
        _global_settings = None


def get_settings() -> Settings:
    if _global_settings is None:
        raise AssertionError("It seems that the settings have not been setup yet.")
    return _global_settings
