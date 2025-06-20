import fnmatch
import glob
import itertools
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from typing import Callable, Dict, Iterator, List, Optional, Sequence, Set, Tuple

import yaml
from robocorp import log

from sema4ai.actions._customization._plugin_manager import PluginManager
from sema4ai.actions._protocols import IAction

DEFAULT_EXCLUSION_PATTERNS = [
    "./.git/**",
    "./.vscode/**",
    "./devdata/**",
    "./output/**",
    "./venv/**",
    "./.venv/**",
    "./.DS_store/**",
    "./**/*.pyc",
    "./**/*.zip",
    "./**/.env",
    "./**/__pycache__",
    "./**/.git",
    "./node_modules/**",
]

MAX_DEPTH = 3


def _check_matches(patterns: List[str], paths: List[str]) -> bool:
    if not patterns and not paths:
        # Matched to the end.
        return True

    if (not patterns and paths) or (patterns and not paths):
        return False

    pattern = patterns[0]
    path = paths[0]

    if not glob.has_magic(pattern):
        if pattern != path:
            return False

    elif pattern == "**":
        if len(patterns) == 1:
            return True  # if ** is the last one it matches anything to the right.

        for i in range(len(paths)):
            # Recursively check the remaining patterns as the
            # current pattern could match any number of paths.
            if _check_matches(patterns[1:], paths[i:]):
                return True

    elif not fnmatch.fnmatch(path, pattern):
        # Current part doesn't match.
        return False

    return _check_matches(patterns[1:], paths[1:])


def _glob_matches_path(
    path: str, pattern: str, sep: str = os.sep, altsep: str | None = os.altsep
):
    if altsep:
        pattern = pattern.replace(altsep, sep)
        path = path.replace(altsep, sep)

    patterns = pattern.split(sep)
    paths = path.split(sep)
    if paths:
        if paths[0] == "":
            paths = paths[1:]
    if patterns:
        if patterns[0] == "":
            patterns = patterns[1:]

    return _check_matches(patterns, paths)


def _convert_glob_patterns(patterns: list[str]) -> list[str]:
    converted_exclusion_patterns = []
    for pat in patterns:
        if pat.startswith("./"):
            # If the user did './b/c', we have to start the match from
            # the current path.
            pat = pat[2:]
        elif pat.startswith("/"):
            # If the user did '/b/c', we have to start the match from
            # the root.
            pat = pat[1:]
        elif not pat.startswith("**"):
            # If the user did not anchor the pattern, make it available to
            # be matched anywhere (i.e.: *.pyc must match .pyc files anywhere).
            pat = f"**/{pat}"

        converted_exclusion_patterns.append(pat)

    return converted_exclusion_patterns


class FindActionPaths:
    """
    Iterator class that finds Python files matching glob patterns (just based on the basename,
    not full path) while avoiding library roots and common directories that should be skipped.
    """

    def __init__(
        self, root_dir: Path, include_patterns: List[str], library_roots: List[str]
    ):
        """
        Initialize the path finder.

        Args:
            root_dir: The root path to search in
            include_patterns: List of glob patterns to match against
            library_roots: List of library root paths to avoid
        """
        self.root_dir = Path(os.path.normcase(os.path.normpath(root_dir))).absolute()
        self.include_patterns: list[str] = _convert_glob_patterns(include_patterns)

        self.library_roots: set[Path] = set(
            Path(os.path.normcase(os.path.normpath(root))).absolute()
            for root in library_roots
        )

        # Load exclusion patterns from package.yaml
        exclusion_patterns = self._load_exclusion_patterns()
        self.exclusion_patterns = _convert_glob_patterns(exclusion_patterns)

    def _load_exclusion_patterns(self) -> List[str]:
        """Load exclusion patterns from package.yaml file."""
        # Find package.yaml starting from current working directory
        package_yaml_path = self.root_dir / "package.yaml"
        if not package_yaml_path.exists():
            # No package.yaml found, return default exclusion patterns
            return DEFAULT_EXCLUSION_PATTERNS

        try:
            with open(package_yaml_path, "r", encoding="utf-8") as f:
                package_data = yaml.safe_load(f)

            # Extract exclusion patterns from packaging.exclude section
            if (
                package_data
                and isinstance(package_data, dict)
                and "packaging" in package_data
                and isinstance(package_data["packaging"], dict)
                and "exclude" in package_data["packaging"]
            ):
                exclude_patterns = package_data["packaging"]["exclude"]
                if isinstance(exclude_patterns, list):
                    return [str(pattern) for pattern in exclude_patterns]

            return DEFAULT_EXCLUSION_PATTERNS

        except Exception as e:
            log.warn(f"Failed to load exclusion patterns from {package_yaml_path}: {e}")
            return DEFAULT_EXCLUSION_PATTERNS

    def _should_exclude(self, path: Path, is_dir: bool) -> bool:
        """Check if a path should be excluded based on the patterns from package.yaml."""
        if not self.exclusion_patterns:
            return False

        relative_path_str = str(path.relative_to(self.root_dir))

        for pattern in self.exclusion_patterns:
            if pattern.endswith("/**"):
                pattern = pattern[:-3]

            if _glob_matches_path(relative_path_str, pattern):
                return True

        return False

    def _file_matches_glob_patterns(self, path: Path) -> bool:
        """Check if a path matches any of the glob patterns."""
        for pattern in self.include_patterns:
            relative_path_str = str(path.relative_to(self.root_dir))
            if _glob_matches_path(relative_path_str, pattern):
                return True

        return False

    def _iterate_paths_recursive(
        self, current_dir: Path, depth: int = 0
    ) -> Iterator[Path]:
        """Recursively iterate through paths, avoiding library roots and excluded paths."""
        try:
            for item in current_dir.iterdir():
                if item.is_file():
                    # Check files at current depth
                    if (
                        item.suffix == ".py"
                        and self._file_matches_glob_patterns(item)
                        and not self._should_exclude(item, False)
                    ):
                        yield item
                elif item.is_dir():
                    # Only recurse into directories if we haven't reached the depth limit
                    if (
                        depth < MAX_DEPTH
                        and item not in self.library_roots
                        and not self._should_exclude(item, True)
                    ):
                        yield from self._iterate_paths_recursive(item, depth + 1)
        except (PermissionError, OSError):
            # Skip directories we can't access
            pass

    def __iter__(self) -> Iterator[Path]:
        """Iterate over all matching Python files."""
        if self.root_dir.is_file():
            # If the input is a python file, don't apply any filtering.
            if self.root_dir.suffix == ".py":
                yield self.root_dir
            return

        yield from self._iterate_paths_recursive(self.root_dir)


def _get_default_library_roots() -> list[str]:
    import site
    import threading

    roots: list[str] = []

    try:
        import sysconfig  # Python 2.7 onwards only.
    except ImportError:
        pass
    else:
        for path_name in set(("stdlib", "platstdlib", "purelib", "platlib")) & set(
            sysconfig.get_path_names()
        ):
            roots.append(sysconfig.get_path(path_name))

    # Make sure we always get at least the standard library location (based on the `os` and
    # `threading` modules -- it's a bit weird that it may be different on the ci, but it happens).
    roots.append(os.path.dirname(os.__file__))
    roots.append(os.path.dirname(threading.__file__))

    if hasattr(site, "getusersitepackages"):
        user_site_packages = site.getusersitepackages()
        if isinstance(user_site_packages, (list, tuple)):
            for site_path in user_site_packages:
                roots.append(site_path)
        else:
            roots.append(user_site_packages)

    if hasattr(site, "getsitepackages"):
        site_packages = site.getsitepackages()
        if isinstance(site_packages, (list, tuple)):
            for site_path in site_packages:
                roots.append(site_path)
        else:
            roots.append(site_packages)

    for path in sys.path:
        if os.path.exists(path) and os.path.basename(path) in (
            "site-packages",
            "pip-global",
        ):
            roots.append(path)

    # Some of the roots may not exist, filter those out.
    roots = [str(path) for path in roots if path is not None]
    # Add the resolved version too.
    roots.extend([os.path.realpath(path) for path in roots])

    return sorted(set(roots))


def module_name_from_path(path: Path, root: Path) -> str:
    """
    Return a dotted module name based on the given path, anchored on root.
    For example: path="projects/src/tests/test_foo.py" and root="/projects", the
    resulting module name will be "src.tests.test_foo".

    Based on: https://github.com/pytest-dev/pytest/blob/main/src/_pytest/pathlib.py
    """
    path = path.with_suffix("")
    try:
        relative_path = path.relative_to(root)
    except ValueError:
        # If we can't get a relative path to root, use the full path, except
        # for the first part ("d:\\" or "/" depending on the platform, for example).
        path_parts = path.parts[1:]
    else:
        # Use the parts for the relative path to the root path.
        path_parts = relative_path.parts

    return ".".join(path_parts)


def insert_missing_modules(modules: Dict[str, ModuleType], module_name: str) -> None:
    """
    Used by ``import_path`` to create intermediate modules.
    When we want to import a module as "src.tests.test_foo" for example, we need
    to create empty modules "src" and "src.tests" after inserting "src.tests.test_foo",
    otherwise "src.tests.test_foo" is not importable by ``__import__``.

    Based on: https://github.com/pytest-dev/pytest/blob/main/src/_pytest/pathlib.py
    """
    import importlib

    module_parts = module_name.split(".")
    while module_name:
        if module_name not in modules:
            try:
                # If sys.meta_path is empty, calling import_module will issue
                # a warning and raise ModuleNotFoundError. To avoid the
                # warning, we check sys.meta_path explicitly and raise the error
                # ourselves to fall back to creating a dummy module.
                if not sys.meta_path:
                    raise ModuleNotFoundError
                importlib.import_module(module_name)
            except ModuleNotFoundError:
                module = ModuleType(
                    module_name,
                    doc="Empty module created by sema4ai-actions.",
                )
                modules[module_name] = module
        module_parts.pop(-1)
        module_name = ".".join(module_parts)


def import_path(
    path: Path,
    *,
    root: Path,
) -> ModuleType:
    """Import and return a module from the given path, which can be a file (a module) or
    a directory (a package).

    Based on: https://github.com/pytest-dev/pytest/blob/main/src/_pytest/pathlib.py
    """
    import importlib.util

    if not path.exists():
        raise ImportError(path)

    path = path.absolute()
    root = root.absolute()
    module_name = module_name_from_path(path, root)
    mod = sys.modules.get(module_name)
    if mod is not None:
        return mod

    for meta_importer in sys.meta_path:
        spec = meta_importer.find_spec(module_name, [str(path.parent)])
        if spec is not None:
            break
    else:
        spec = importlib.util.spec_from_file_location(module_name, str(path))

    if spec is None:
        raise ImportError(
            f"Can't find module '{module_name}'\n  at location '{path}'\n  (with root: '{root}')."
        )
    try:
        mod = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = mod
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
    except Exception:
        log.critical(
            f"Error when importing module '{module_name}'\n  at location '{path}'\n  (with root: '{root}')."
        )
        raise
    insert_missing_modules(sys.modules, module_name)
    return mod


@contextmanager
def _add_to_sys_path_0(root: Path):
    """
    This context manager may be used to raise priority for some folder so that
    it imports the contents inside it with priority.
    """
    sys.path.insert(0, str(root))
    try:
        yield
    finally:
        try:
            sys.path.remove(str(root))
        except ValueError:
            pass


# These are the actions found. They're kept in a global variable because when
# doing multiple invocations of the main we want to consider those properly.
_methods_marked_as_actions_found: List[Tuple[Callable, Dict]] = []
_found_as_set: Set[Tuple[str, str]] = set()


def clear_previously_collected_actions():
    _methods_marked_as_actions_found.clear()
    _found_as_set.clear()


def collect_actions(
    pm: PluginManager,
    path: Path,
    action_names: Sequence[str] = (),
    glob: Optional[str] = None,
) -> Iterator[IAction]:
    """
    Note: collecting actions is not thread-safe.

    Raises: ActionsCollectError
    """
    import re

    from sema4ai.actions import _constants, _hooks

    path = path.absolute()
    action_names_as_set = set(action_names)

    _hooks.before_collect_actions(path, action_names_as_set)

    def accept_action(action: IAction):
        if not action_names:
            return True

        return action.name in action_names

    def on_func_found(func, options: Dict):
        from sema4ai.actions._exceptions import ActionsError

        key = (func.__code__.co_name, func.__code__.co_filename)
        if key in _found_as_set:
            raise ActionsError(
                f"Error: an action with the name '{func.__code__.co_name}' was "
                + f"already found in: {func.__code__.co_filename}."
            )
        _found_as_set.add(key)

        _methods_marked_as_actions_found.append(
            (
                func,
                options,
            )
        )

    with _hooks.on_action_func_found.register(on_func_found):
        if path.is_dir():
            root = _get_root(path, is_dir=True)
            with _add_to_sys_path_0(root):
                package_init = path / "__init__.py"
                lst = []
                if package_init.exists():
                    lst.append(package_init)

                use_glob = glob or _constants.DEFAULT_ACTION_SEARCH_GLOB

                # We want to accept '|' in glob.
                globs = use_glob.split("|")

                # Use the new FindActionPaths class to find files
                library_roots = _get_default_library_roots()
                finder = FindActionPaths(path, globs, library_roots)
                found_paths: list[Path] = list(finder)
                found_paths = sorted(found_paths, key=lambda x: x.as_posix())

                compiled_re = re.compile(_constants.REGEXP_TO_LOAD_FOR_DEFINITIONS)

                for path_with_action in itertools.chain(lst, found_paths):
                    if path_with_action.is_dir() or not path_with_action.name.endswith(
                        ".py"
                    ):
                        continue

                    try:
                        with open(path_with_action, "r", encoding="utf-8") as f:
                            content = f.read()
                            if not compiled_re.search(content):
                                continue
                    except Exception:
                        log.exception(
                            f"Error when trying to read file: {path_with_action}"
                        )
                        continue

                    import_path(path_with_action, root=root)

        elif path.is_file():
            root = _get_root(path, is_dir=False)
            with _add_to_sys_path_0(root):
                import_path(path, root=root)

        else:
            from ._exceptions import ActionsCollectError

            if not path.exists():
                raise ActionsCollectError(f"Path: {path} does not exist")

            raise ActionsCollectError(f"Expected {path} to map to a directory or file.")

    from sema4ai.actions._action import Action

    all_actions: List[IAction] = []
    for method, options in _methods_marked_as_actions_found:
        module_name = method.__module__
        module_file = method.__code__.co_filename

        action = Action(pm, module_name, module_file, method, options=options)

        if accept_action(action):
            all_actions.append(action)
            yield action

    _hooks.after_collect_actions(all_actions)


def update_pythonpath(path: Path) -> None:
    check_path = path
    while True:
        # If a `package.yaml`` is found, that should be the used path.
        if (check_path / "package.yaml").exists():
            add = str(check_path)
            if add not in sys.path:
                sys.path.insert(0, add)
            return

        new_path = check_path.parent
        if not new_path or new_path == check_path:
            # Did not find a package.yaml: add the cwd to the pythonpath
            add = os.path.abspath(".")
            if add not in sys.path:
                sys.path.insert(0, add)
            return
        else:
            check_path = new_path


def _get_root(path: Path, is_dir: bool) -> Path:
    pythonpath_entries = tuple(Path(p) for p in sys.path)
    initial = path
    while True:
        # Try to find a parent which is in the pythonpath
        for p in pythonpath_entries:
            try:
                if os.path.samefile(p, path):
                    return p.absolute()
            except OSError:
                pass

        new_path = path.parent
        if not new_path or new_path == path:
            if is_dir:
                return initial.absolute()
            else:
                return initial.parent.absolute()

        path = new_path
