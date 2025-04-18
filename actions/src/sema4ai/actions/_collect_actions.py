import itertools
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from typing import Callable, Dict, Iterator, List, Optional, Sequence, Set, Tuple

from robocorp import log

from sema4ai.actions._customization._plugin_manager import PluginManager
from sema4ai.actions._protocols import IAction


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

                # Use predictable order when loading modules.
                found_globs = []
                for g in globs:
                    for p in path.rglob(g):
                        found_globs.append(p)
                found_globs = sorted(found_globs, key=lambda x: x.as_posix())

                for path_with_action in itertools.chain(lst, found_globs):
                    if path_with_action.is_dir() or not path_with_action.name.endswith(
                        ".py"
                    ):
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

    for method, options in _methods_marked_as_actions_found:
        module_name = method.__module__
        module_file = method.__code__.co_filename

        action = Action(pm, module_name, module_file, method, options=options)

        if accept_action(action):
            yield action


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
