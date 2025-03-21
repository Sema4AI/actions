from pathlib import Path


def make_entitlements_file(target_dir: Path) -> Path:
    """
    Creates an entitlements file in the target directory.
    """
    contents = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.allow-dyld-environment-variables</key>
    <true/>
  </dict>
</plist>
"""
    entitlements_path = target_dir / "entitlements.mac.plist"
    entitlements_path.write_text(contents)
    return entitlements_path
