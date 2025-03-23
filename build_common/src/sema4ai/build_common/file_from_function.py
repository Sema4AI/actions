import inspect
from pathlib import Path


def make_file_with_function_contents(func, target: Path) -> Path:
    name = func.__name__
    print(f"Creating file {target} with function contents of: {name}")
    source_lines, _ = inspect.getsourcelines(func)

    # First, find the "def" line.
    def_lineno = 0
    for line in source_lines:
        line = line.strip()
        if line.startswith("def") and line.endswith(":"):
            break
        def_lineno += 1
    else:
        raise ValueError("Failed to locate function header.")

    # Remove everything up to and including "def".
    source_lines = source_lines[def_lineno + 1 :]
    assert source_lines

    # Now we need to adjust indentation. Compute how much the first line of
    # the body is indented by, then dedent all lines by that amount. Blank
    # lines don't matter indentation-wise, and might not be indented to begin
    # with, so just replace them with a simple newline.
    for line in source_lines:
        if line.strip():
            break  # i.e.: use first non-empty line
    indent = len(line) - len(line.lstrip())
    source_lines = [line[indent:] if line.strip() else "\n" for line in source_lines]
    source = "".join(source_lines)

    # Write it to file.
    target.write_text(source)
    return target
