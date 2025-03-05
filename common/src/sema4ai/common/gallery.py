from pathlib import Path
from typing import Any, TypedDict

from sema4ai.common.null import NULL
from sema4ai.common.protocols import ActionResult, IMonitor


class _ListPackageVersionMetadata(TypedDict):
    version: str
    name: str
    description: str
    zip: str


class _PackageVersionMetadata(TypedDict):
    version: str
    description: str
    zip: str


class _PackageMetadata(TypedDict):
    name: str
    versions: list[_PackageVersionMetadata]


class _PackageMetadataRoot(TypedDict):
    packages: dict[str, _PackageMetadata]


class _PackageListInfo(TypedDict):
    name: str
    zip_url: str
    description: str


class GalleryActionPackages:
    _metadata: _PackageMetadataRoot | None

    def __init__(self, metadata: dict | None = None):
        if metadata is not None:
            self._metadata = self._validate_metadata(metadata)
        else:
            self._metadata = None

    def extract_package(
        self, package_name: str, target_dir: Path, monitor: IMonitor = NULL
    ) -> ActionResult[str]:
        from .text import slugify

        try:
            import json

            packages_result = self.list_packages()
            if not packages_result.success:
                return ActionResult.make_failure(
                    packages_result.message or "Unknown error"
                )

            packages = packages_result.result
            if not packages:
                return ActionResult.make_failure("No packages found in metadata")

            package_metadata = packages.get(package_name)
            if not package_metadata:
                return ActionResult.make_failure(
                    f"Package {package_name} not found in metadata"
                )

            use_package_name = package_metadata.get("name")
            if not use_package_name:
                return ActionResult.make_failure(
                    f"Package {package_name} has no name in metadata. Found: {json.dumps(package_metadata, indent=2)}"
                )

            use_dir = target_dir / slugify(use_package_name)

            if package_metadata.get("zip") is None:
                return ActionResult.make_failure(
                    f"Package {package_name} has no zip url in metadata. Found: {json.dumps(package_metadata, indent=2)}"
                )

            import sema4ai_http

            try:
                response = sema4ai_http.get(package_metadata["zip"])
                if response.status != 200:
                    raise Exception(
                        f"Failed to download package {package_name}. Status: {response.status}. Data: {response.data.decode('utf-8', errors='backslashreplace')}"
                    )
            except Exception as e:
                msg = f"Could not download package {package_name}. Reason: {e}"
                return ActionResult.make_failure(msg)

            # Extract the zip file (from the response) directly to the target directory
            import io
            import zipfile

            bytesio = io.BytesIO(response.data)
            use_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(bytesio, "r") as zip_ref:
                zip_ref.extractall(use_dir)

            return ActionResult.make_success(str(use_dir))
        except Exception as e:
            msg = f"Could not extract package {package_name}. Reason: {e}"
            return ActionResult.make_failure(msg)

    def list_packages(self) -> ActionResult[dict[str, _ListPackageVersionMetadata]]:
        """
        Returns a dict where the key is the package name and the value
        has the description and the zip url to download the package.
        """
        result = self._load_metadata()
        if not result.success:
            return ActionResult.make_failure(result.message or "Unknown error")

        metadata = result.result
        assert metadata is not None
        packages: dict[str, _PackageMetadata] = metadata["packages"]

        ret: dict[str, _ListPackageVersionMetadata] = {}
        for package_name, package in packages.items():
            for version in package["versions"]:
                ret[f"{package_name} {version['version']}"] = {
                    "name": package_name,
                    "version": version["version"],
                    "description": version["description"],
                    "zip": version["zip"],
                }

        return ActionResult.make_success(ret)

    def _validate_metadata(self, metadata: Any) -> _PackageMetadataRoot:
        assert isinstance(metadata, dict), "Metadata is not a dictionary"
        packages = metadata["packages"]
        assert isinstance(packages, dict), "Metadata 'packages' is not a dictionary"

        for key, entry in packages.items():
            assert isinstance(
                entry, dict
            ), f"Metadata 'packages' entry {key} is not a dictionary"

            if "versions" not in entry:
                raise ValueError(
                    f"Metadata 'packages' entry {key} is missing 'versions'"
                )

            if "name" not in entry:
                raise ValueError(f"Metadata 'packages' entry {key} is missing 'name'")

            versions = entry["versions"]
            for version in versions:
                assert isinstance(
                    version, dict
                ), f"Metadata 'versions' entry {key} is not a dictionary. Found: {version}"

                if "zip" not in version:
                    raise ValueError(
                        f"Metadata 'versions' entry {key} is missing 'zip'"
                    )

                if "version" not in version:
                    raise ValueError(
                        f"Metadata 'versions' entry {key} is missing 'version'"
                    )

                if "description" not in version:
                    raise ValueError(
                        f"Metadata 'versions' entry {key} is missing 'description'"
                    )

        return metadata  # type: ignore

    def _load_metadata(self) -> ActionResult[_PackageMetadataRoot]:
        """
        Loads the metadata from the gallery (if not already loaded) and returns it.

        May throw an exception if the metadata cannot be loaded.
        """
        from sema4ai_http import get

        if self._metadata:
            # Ok, we have loaded it before
            assert isinstance(
                self._metadata, dict
            ), f"Expected metadata to be a dict. Found: {self._metadata}"
            return ActionResult.make_success(self._metadata)

        try:
            # Try to get it fresh from the internet (we'll have to get the actual data from the
            # net afterwards, so, not much point in caching it)
            response = get("https://cdn.sema4.ai/gallery/actions/manifest.json")
            if response.status != 200:
                raise Exception(
                    f"Failed to download gallery actions metadata. Status: {response.status}. Data: {response.data.decode('utf-8', errors='backslashreplace')}"
                )
            metadata = response.json()
            self._metadata = self._validate_metadata(metadata)
            assert isinstance(self._metadata, dict)
            return ActionResult.make_success(self._metadata)
        except Exception as e:
            msg = f"Could not download gallery actions metadata. Reason: {e}"
            return ActionResult.make_failure(msg)
