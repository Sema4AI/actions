"""
This package should be independent of the rest as we can potentially make
it a standalone package in the future (maybe with a command line UI).
"""

import pathlib
import typing
from collections.abc import Iterator
from typing import Optional, Union

from ..ls_protocols import _DiagnosticSeverity, _DiagnosticsTypedDict
from ._deps_protocols import ICondaCloud, IPyPiCloud

if typing.TYPE_CHECKING:
    from ._conda_deps import CondaDepInfo, CondaDeps
    from ._package_deps import PackageDepsConda, PackageDepsPip
    from ._pip_deps import PipDepInfo, PipDeps


class BaseAnalyzer:
    _pypi_cloud: IPyPiCloud
    _conda_cloud: ICondaCloud

    _pip_deps: "Union[PipDeps, PackageDepsPip]"
    _conda_deps: "Union[CondaDeps, PackageDepsConda]"

    def __init__(
        self,
        contents: str,
        path: str,
        conda_cloud: ICondaCloud,
        pypi_cloud: IPyPiCloud | None = None,
    ):
        """
        Args:
            contents: The contents of the conda.yaml/action-server.yaml.
            path: The path for the conda yaml.
        """
        from .pypi_cloud import PyPiCloud

        self.contents = contents
        self.path = path

        self._loaded_yaml = False
        self._load_errors: list[_DiagnosticsTypedDict] = []
        self._yaml_data: dict | None = None

        if pypi_cloud is None:
            self._pypi_cloud = PyPiCloud()
        else:
            self._pypi_cloud = pypi_cloud

        self._conda_cloud = conda_cloud

    def _load_yaml_info(self) -> None:
        """
        Loads the base information and creates errors for syntax errors
        loading the yaml.
        """

        if self._loaded_yaml:
            return
        self._loaded_yaml = True

        from yaml.error import MarkedYAMLError

        from ..yaml_with_location import LoaderWithLines, create_range_from_location

        diagnostic: _DiagnosticsTypedDict

        try:
            loader = LoaderWithLines(self.contents)
            path: pathlib.Path = pathlib.Path(self.path)

            loader.name = f".../{path.parent.name}/{path.name}"
            data = loader.get_single_data()
            if isinstance(data, dict):
                self._yaml_data = data
            else:
                diagnostic = {
                    "range": create_range_from_location(0, 0),
                    "severity": _DiagnosticSeverity.Error,
                    "source": "sema4ai",
                    "message": "Error: expected dict to be root of yaml",
                }
                self._load_errors.append(diagnostic)

        except MarkedYAMLError as e:
            if e.problem_mark:
                diagnostic = {
                    "range": create_range_from_location(
                        e.problem_mark.line, e.problem_mark.column
                    ),
                    "severity": _DiagnosticSeverity.Error,
                    "source": "sema4ai",
                    "message": f"Syntax error: {e}",
                }
                self._load_errors.append(diagnostic)

    def iter_pip_issues(self):
        from .pip_impl import pip_packaging_version

        for dep_info in self._pip_deps.iter_deps_infos():
            if dep_info.error_msg:
                diagnostic = {
                    "range": dep_info.dep_range,
                    "severity": _DiagnosticSeverity.Error,
                    "source": "sema4ai",
                    "message": dep_info.error_msg,
                }

                yield diagnostic

                continue

            if dep_info.constraints and len(dep_info.constraints) == 1:
                # For now just checking versions '=='.
                constraint = next(iter(dep_info.constraints))
                if constraint[0] == "==":
                    local_version = constraint[1]
                    newer_cloud_versions = self._pypi_cloud.get_versions_newer_than(
                        dep_info.name, pip_packaging_version.parse(local_version)
                    )
                    if newer_cloud_versions:
                        latest_cloud_version = newer_cloud_versions[-1]
                        diagnostic = {
                            "range": dep_info.dep_range,
                            "severity": _DiagnosticSeverity.Warning,
                            "source": "sema4ai",
                            "message": f"Consider updating '{dep_info.name}' to the latest version: '{latest_cloud_version}'. "
                            + f"Found {len(newer_cloud_versions)} versions newer than the current one: {', '.join(newer_cloud_versions)}.",
                        }

                        yield diagnostic

    def iter_conda_issues(self) -> Iterator[_DiagnosticsTypedDict]:
        from .conda_cloud import sort_conda_versions
        from .conda_impl.conda_version import VersionSpec

        diagnostic: _DiagnosticsTypedDict
        dep_vspec = self._conda_deps.get_dep_vspec("python")

        # See: https://devguide.python.org/versions/

        if dep_vspec is not None:
            # We have the dep spec, not the actual version
            # (so, it could be something as >3.3 <4)
            # So, if an old version may be gotten from that spec, we warn about it.
            vspec = VersionSpec(dep_vspec)
            for old_version in "2 3.1 3.2 3.3 3.4 3.5 3.6 3.7".split(" "):
                if vspec.match(old_version):
                    dep_range = self._conda_deps.get_dep_range("python")

                    diagnostic = {
                        "range": dep_range,
                        "severity": _DiagnosticSeverity.Warning,
                        "source": "sema4ai",
                        "message": "The official support for versions lower than Python 3.8 has ended. "
                        + " It is advisable to transition to a newer version "
                        + "(Python 3.9 or newer is recommended).",
                    }

                    yield diagnostic
                    break

        dep_vspec = self._conda_deps.get_dep_vspec("pip")

        if dep_vspec is not None:
            vspec = VersionSpec(dep_vspec)
            # pip should be 22 or newer, so, check if an older version matches.
            for old_version in (str(x) for x in range(1, 22)):
                if vspec.match(old_version):
                    dep_range = self._conda_deps.get_dep_range("pip")

                    diagnostic = {
                        "range": dep_range,
                        "severity": _DiagnosticSeverity.Warning,
                        "source": "sema4ai",
                        "message": "Consider updating pip to a newer version (at least pip 22 onwards is recommended).",
                    }

                    yield diagnostic
                    break

        sqlite_queries = self._conda_cloud.sqlite_queries()
        if sqlite_queries:
            with sqlite_queries.db_cursors() as db_cursors:
                for conda_dep in self._conda_deps.iter_deps_infos():
                    if conda_dep.name in ("python", "pip", "uv"):
                        continue

                    if conda_dep.error_msg:
                        diagnostic = {
                            "range": conda_dep.dep_range,
                            "severity": _DiagnosticSeverity.Error,
                            "source": "sema4ai",
                            "message": conda_dep.error_msg,
                        }

                        yield diagnostic

                        continue

                    version_spec = conda_dep.get_dep_vspec()
                    if version_spec is None:
                        continue

                    versions = sqlite_queries.query_versions(conda_dep.name, db_cursors)
                    if not versions:
                        continue

                    sorted_versions = sort_conda_versions(versions)
                    last_version = sorted_versions[-1]
                    if not version_spec.match(last_version):
                        # The latest version doesn't match, let's show a warning.
                        newer_cloud_versions = []
                        for v in reversed(sorted_versions):
                            if not version_spec.match(v):
                                newer_cloud_versions.append(v)
                            else:
                                break

                        diagnostic = {
                            "range": conda_dep.dep_range,
                            "severity": _DiagnosticSeverity.Warning,
                            "source": "sema4ai",
                            "message": f"Consider updating '{conda_dep.name}' to match the latest version: '{last_version}'. "
                            + f"Found {len(newer_cloud_versions)} versions that don't match the version specification: {', '.join(newer_cloud_versions)}.",
                        }

                        yield diagnostic

    def find_pip_dep_at(self, line, col) -> "Optional[PipDepInfo]":
        """
        Args:
            line: 0-based line
        """
        from ..yaml_with_location import is_inside

        self._load_yaml_info()
        for dep_info in self._pip_deps.iter_deps_infos():
            if is_inside(dep_info.dep_range, line, col):
                return dep_info
        return None

    def find_conda_dep_at(self, line, col) -> "Optional[CondaDepInfo]":
        from ..yaml_with_location import is_inside

        self._load_yaml_info()
        for dep_info in self._conda_deps.iter_deps_infos():
            if is_inside(dep_info.dep_range, line, col):
                return dep_info
        return None


def extract_range(*items):
    from ..yaml_with_location import create_range_from_location

    for item in items:
        if hasattr(item, "as_range"):
            return item.as_range()
    return create_range_from_location(0, 0)


def type_repr(obj):
    # Needed to deal with the `str_with_location`, `dict_with_location`, etc.
    if isinstance(obj, str):
        return "str"
    elif isinstance(obj, bool):
        return "bool"
    elif isinstance(obj, int):
        return "int"
    elif isinstance(obj, float):
        return "float"
    elif isinstance(obj, list):
        return "list"
    elif isinstance(obj, dict):
        return "dict"
    elif isinstance(obj, tuple):
        return "tuple"
    try:
        return type(obj).__name__
    except Exception:
        return str(type(obj))


class PackageYamlAnalyzer(BaseAnalyzer):
    def __init__(
        self,
        contents: str,
        path: str,
        conda_cloud: ICondaCloud,
        pypi_cloud: IPyPiCloud | None = None,
    ):
        from ._package_deps import PackageDepsConda, PackageDepsPip

        self._pip_deps = PackageDepsPip()
        self._conda_deps = PackageDepsConda()
        self._additional_load_errors: list[_DiagnosticsTypedDict] = []

        BaseAnalyzer.__init__(self, contents, path, conda_cloud, pypi_cloud=pypi_cloud)

    def iter_package_yaml_issues(self) -> Iterator[_DiagnosticsTypedDict]:
        self._load_yaml_info()
        if self._load_errors:
            yield from iter(self._load_errors)
            return

        data = self._yaml_data
        if not data:
            return

        yield from iter(self._additional_load_errors)
        yield from self.iter_conda_issues()
        yield from self.iter_pip_issues()
        yield from self._iter_external_endpoints_issues()

    def _iter_external_endpoints_issues(self) -> Iterator[_DiagnosticsTypedDict]:
        from ..yaml_with_location import dict_with_location

        data = self._yaml_data
        if not data:
            return

        external_endpoints = data.get("external-endpoints")
        if not external_endpoints:
            return

        if not isinstance(external_endpoints, list):
            yield {
                "range": extract_range(external_endpoints),
                "severity": _DiagnosticSeverity.Error,
                "source": "sema4ai",
                "message": f"Error: expected 'external-endpoints' to be a list. Found: {external_endpoints!r}",
            }
            return  # Unable to proceed

        expected_keys = {"name", "description", "additional-info-link", "rules"}
        endpoint: dict_with_location
        for endpoint in external_endpoints:
            if not isinstance(endpoint, dict):
                yield {
                    "range": extract_range(endpoint),
                    "severity": _DiagnosticSeverity.Error,
                    "source": "sema4ai",
                    "message": f"Error: 'external-endpoint' must be a dictionary. Found: {endpoint!r}",
                }
                continue  # Unable to proceed

            # Check for unexpected keys
            unexpected_keys = set(endpoint.keys()) - expected_keys
            if unexpected_keys:
                yield {
                    "range": extract_range(endpoint),
                    "severity": _DiagnosticSeverity.Warning,
                    "source": "sema4ai",
                    "message": f"Warning: unexpected key(s) in 'external-endpoint': {sorted(unexpected_keys)}. Expected keys are: {sorted(expected_keys)}.",
                }

            # Validate required fields
            if "name" not in endpoint:
                yield {
                    "range": extract_range(endpoint),
                    "severity": _DiagnosticSeverity.Error,
                    "source": "sema4ai",
                    "message": "Error: 'name' is required and must be a string in 'external-endpoint'.",
                }
            elif not isinstance(endpoint["name"], str):
                yield {
                    "range": extract_range(endpoint["name"], endpoint),
                    "severity": _DiagnosticSeverity.Error,
                    "source": "sema4ai",
                    "message": f"Error: 'name' must be a string in 'external-endpoint'. Found: {endpoint['name']!r} (type: {type_repr(endpoint['name'])})",
                }

            if "description" not in endpoint:
                yield {
                    "range": extract_range(endpoint),
                    "severity": _DiagnosticSeverity.Error,
                    "source": "sema4ai",
                    "message": "Error: 'description' is required in 'external-endpoint'.",
                }
            elif not isinstance(endpoint["description"], str):
                yield {
                    "range": extract_range(endpoint["description"], endpoint),
                    "severity": _DiagnosticSeverity.Error,
                    "source": "sema4ai",
                    "message": f"Error: 'description' must be a string in 'external-endpoint'. Found: {endpoint['description']!r}",
                }

            # Validate optional fields
            if "additional-info-link" in endpoint and not isinstance(
                endpoint["additional-info-link"], str
            ):
                additional_info_link = endpoint["additional-info-link"]
                yield {
                    "range": extract_range(additional_info_link, endpoint),
                    "severity": _DiagnosticSeverity.Error,
                    "source": "sema4ai",
                    "message": f"Error: 'additional-info-link' must be a string if provided. Found: {additional_info_link!r} (type: {type_repr(additional_info_link)})",
                }

            if "rules" in endpoint:
                rules = endpoint["rules"]
                if not isinstance(rules, list):
                    yield {
                        "range": extract_range(rules, endpoint),
                        "severity": _DiagnosticSeverity.Error,
                        "source": "sema4ai",
                        "message": f"Error: 'rules' must be a list if provided. Found: {rules!r} (type: {type_repr(rules)})",
                    }
                else:
                    for rule in rules:
                        if not isinstance(rule, dict):
                            yield {
                                "range": extract_range(rule, endpoint),
                                "severity": _DiagnosticSeverity.Error,
                                "source": "sema4ai",
                                "message": f"Error: each rule in 'rules' must be a dictionary. Found: {rule!r} (type: {type_repr(rule)})",
                            }
                            continue

                        if "host" in rule and not isinstance(rule["host"], str):
                            yield {
                                "range": extract_range(rule.get("host"), rule),
                                "severity": _DiagnosticSeverity.Error,
                                "source": "sema4ai",
                                "message": f"Error: 'host' must be a string if provided in a rule. Found: {rule['host']!r} (type: {type_repr(rule['host'])})",
                            }

                        if "port" in rule:
                            if not isinstance(rule["port"], int) or not (
                                0 <= rule["port"] <= 65535
                            ):
                                yield {
                                    "range": extract_range(rule.get("port"), rule),
                                    "severity": _DiagnosticSeverity.Error,
                                    "source": "sema4ai",
                                    "message": f"Error: 'port' must be a valid integer between 0 and 65535 if provided in a rule. Found: {rule['port']!r} (type: {type_repr(rule['port'])})",
                                }

    def _load_yaml_info(self) -> None:
        if self._loaded_yaml:
            return

        from ..yaml_with_location import (
            create_range_from_location,
            str_with_location,
            str_with_location_capture,
        )

        BaseAnalyzer._load_yaml_info(self)
        data = self._yaml_data
        if not data:
            return

        diagnostic: _DiagnosticsTypedDict
        dependencies_key_entry: str_with_location_capture = str_with_location_capture(
            "dependencies"
        )

        dependencies = data.get(dependencies_key_entry)
        if dependencies is None:
            diagnostic = {
                "range": create_range_from_location(0, 0),
                "severity": _DiagnosticSeverity.Error,
                "source": "sema4ai",
                "message": "Error: 'dependencies' entry not found",
            }
            self._additional_load_errors.append(diagnostic)
            return

        if not dependencies:
            diagnostic = {
                "range": create_range_from_location(0, 0),
                "severity": _DiagnosticSeverity.Error,
                "source": "sema4ai",
                "message": "Error: 'dependencies' entry must not be empty",
            }
            self._additional_load_errors.append(diagnostic)

        elif not isinstance(dependencies, dict):
            diagnostic = {
                "range": create_range_from_location(0, 0),
                "severity": _DiagnosticSeverity.Error,
                "source": "sema4ai",
                "message": f"Error: expected 'dependencies' entry to be a dict (with 'conda-forge' and 'pypi' entries). Found: '{type_repr(dependencies)}'",
            }
            self._additional_load_errors.append(diagnostic)
        else:
            for dep_name, dep in dependencies.items():
                if isinstance(dep_name, str_with_location):
                    if dep_name == "pypi":
                        if not isinstance(dep, list):
                            diagnostic = {
                                "range": dep_name.as_range(),
                                "severity": _DiagnosticSeverity.Error,
                                "source": "sema4ai",
                                "message": f"Error: expected the entries of pypi to be a list. Found: {type_repr(dep)}",
                            }
                            self._additional_load_errors.append(diagnostic)
                            continue

                        for entry in dep:
                            if not isinstance(entry, str_with_location):
                                diagnostic = {
                                    "range": dep_name.as_range(),
                                    "severity": _DiagnosticSeverity.Error,
                                    "source": "sema4ai",
                                    "message": f"Error: expected the entries of pypi to be strings. Found: {type_repr(entry)}: {entry}",
                                }
                                self._additional_load_errors.append(diagnostic)
                                continue

                            if entry.replace(" ", "") == "--use-feature=truststore":
                                diagnostic = {
                                    "range": entry.as_range(),
                                    "severity": _DiagnosticSeverity.Warning,
                                    "source": "sema4ai",
                                    "message": (
                                        "--use-feature=truststore flag does not need to "
                                        "be specified (it is automatically used when a "
                                        '"robocorp-truststore" or "truststore" dependency is added).'
                                    ),
                                }
                                self._additional_load_errors.append(diagnostic)
                                continue

                            if entry.startswith("--"):
                                diagnostic = {
                                    "range": entry.as_range(),
                                    "severity": _DiagnosticSeverity.Error,
                                    "source": "sema4ai",
                                    "message": f"Invalid entry in pypi: {entry}",
                                }
                                self._additional_load_errors.append(diagnostic)
                                continue

                            self._pip_deps.add_dep(entry, entry.as_range())

                    elif dep_name == "conda-forge":
                        for entry in dep:
                            if not isinstance(entry, str_with_location):
                                diagnostic = {
                                    "range": dep_name.as_range(),
                                    "severity": _DiagnosticSeverity.Error,
                                    "source": "sema4ai",
                                    "message": f"Error: expected the entries of conda-forge to be strings. Found: {type_repr(entry)}: {entry}",
                                }
                                self._additional_load_errors.append(diagnostic)
                                continue

                            self._conda_deps.add_dep(entry, entry.as_range())

                    else:
                        diagnostic = {
                            "range": dep_name.as_range(),
                            "severity": _DiagnosticSeverity.Error,
                            "source": "sema4ai",
                            "message": (
                                "Error: only expected children are pypi and conda (dict entries). "
                                f"Found: {dep_name}"
                            ),
                        }
                        self._additional_load_errors.append(diagnostic)
                else:
                    diagnostic = {
                        "range": dependencies_key_entry.as_range(),
                        "severity": _DiagnosticSeverity.Error,
                        "source": "sema4ai",
                        "message": "Error: found unexpected entry in dependencies.",
                    }
                    self._additional_load_errors.append(diagnostic)


class CondaYamlAnalyzer(BaseAnalyzer):
    def __init__(
        self,
        contents: str,
        path: str,
        conda_cloud: ICondaCloud,
        pypi_cloud: IPyPiCloud | None = None,
    ):
        from ._conda_deps import CondaDeps
        from ._pip_deps import PipDeps

        self._pip_deps = PipDeps()
        self._conda_deps = CondaDeps()

        BaseAnalyzer.__init__(self, contents, path, conda_cloud, pypi_cloud=pypi_cloud)

    def _load_yaml_info(self) -> None:
        if self._loaded_yaml:
            return

        from ..yaml_with_location import str_with_location

        BaseAnalyzer._load_yaml_info(self)
        data = self._yaml_data
        if not data:
            return

        dependencies = data.get("dependencies")

        conda_versions = self._conda_deps
        pip_versions = self._pip_deps
        if dependencies:
            for dep in dependencies:
                # At this level we're seeing conda versions. The spec is:
                # https://docs.conda.io/projects/conda-build/en/latest/resources/package-spec.html#package-match-specifications
                # A bunch of code from conda was copied to handle that so that we
                # can just `conda_match_spec.parse_spec_str` to identify the version
                # we're dealing with.
                if isinstance(dep, str_with_location):
                    conda_versions.add_dep(dep, dep.as_range())
                elif isinstance(dep, dict):
                    pip_deps = dep.get("pip")
                    if pip_deps:
                        for dep in pip_deps:
                            if isinstance(dep, str_with_location) and isinstance(
                                dep, str
                            ):
                                pip_versions.add_dep(dep, dep.as_range())

    def iter_conda_yaml_issues(self) -> Iterator[_DiagnosticsTypedDict]:
        self._load_yaml_info()
        if self._load_errors:
            yield from iter(self._load_errors)
            return

        data = self._yaml_data
        if not data:
            return

        yield from self.iter_conda_issues()
        yield from self.iter_pip_issues()
