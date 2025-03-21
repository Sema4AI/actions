from pathlib import Path


def zip_go_wrapper_assets(src_path: Path, assets_dir: Path):
    """
    Get the assets from the build-binary and zip them up.

    Args:
        src_path: The path to the directory containing the assets (dist/<project-name>)
        assets_dir: The path to the directory to save the zip file
            (usually ROOT_DIR / "go-wrapper" / "assets")
    """
    import hashlib
    import zipfile

    if not src_path.exists():
        raise RuntimeError(f"Source path does not exist: {src_path}")

    zip_path = assets_dir / "assets.zip"

    if zip_path.exists():
        zip_path.unlink()

    print(f"Zipping assets from {src_path} to {zip_path}")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in src_path.rglob("*"):
            if file.is_file():
                zf.write(file, file.relative_to(src_path))
    print(f"Zipped assets to {zip_path}")

    zip_hash = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    zip_hash_file = assets_dir / "app_hash"
    zip_hash_file.write_text(zip_hash)
    print(f"Wrote zip hash to {zip_hash_file}")


def write_version_to_go_wrapper(assets_dir: Path, version: str):
    """
    Write the version to the go-wrapper/version.txt file.
    """
    v_file = assets_dir / "version.txt"
    v_file.write_text(version)
    print(f"Wrote version {version} to {v_file}")
