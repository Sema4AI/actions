import yaml

from .ls_protocols import _RangeTypedDict


def create_range_from_location(
    start_line: int,
    start_col: int,
    end_line: int | None = None,
    end_col: int | None = None,
) -> _RangeTypedDict:
    """
    If the end_line and end_col aren't passed we consider
    that the location should go up until the end of the line.
    """
    if end_line is None:
        assert end_col is None
        end_line = start_line + 1
        end_col = 0
    assert end_col is not None
    dct: _RangeTypedDict = {
        "start": {
            "line": start_line,
            "character": start_col,
        },
        "end": {
            "line": end_line,
            "character": end_col,
        },
    }
    return dct


class str_with_location(str):
    # location: tuple(start_line, start_col, end_line, end_col)
    location: tuple[int, int, int, int] | None = None

    @property
    def scalar(self):
        return self

    def as_range(self) -> _RangeTypedDict:
        assert self.location
        start_line, start_col, end_line, end_col = self.location
        return create_range_from_location(start_line, start_col, end_line, end_col)


class str_with_location_capture(str_with_location):
    """
    The point of this class is that when a `str_with_location` is in a dict
    and we get the dict value, we don't really have access to the dict key to
    get the key location.

    As such, this class can be used to automatically obtain the location of
    the matched key when `__eq__` is called without requiring access to the
    actual key object (which is stored in the dict).
    """

    def __eq__(self, value: object) -> bool:
        equals = str.__eq__(self, value)
        if equals and hasattr(value, "location"):
            self.location = value.location
        return equals

    def __hash__(self) -> int:
        return str.__hash__(self)


class int_with_location(int):
    # location: tuple(start_line, start_col, end_line, end_col)
    location: tuple[int, int, int, int] | None = None

    @property
    def scalar(self):
        return self

    def as_range(self) -> _RangeTypedDict:
        assert self.location
        start_line, start_col, end_line, end_col = self.location
        return create_range_from_location(start_line, start_col, end_line, end_col)


class dict_with_location(dict):
    # location: tuple(start_line, start_col, end_line, end_col)
    location: tuple[int, int, int, int] | None = None

    def as_range(self) -> _RangeTypedDict:
        assert self.location
        start_line, start_col, end_line, end_col = self.location
        return create_range_from_location(start_line, start_col, end_line, end_col)


class float_with_location(float):
    # location: tuple(start_line, start_col, end_line, end_col)
    location: tuple[int, int, int, int] | None = None

    def as_range(self) -> _RangeTypedDict:
        assert self.location
        start_line, start_col, end_line, end_col = self.location
        return create_range_from_location(start_line, start_col, end_line, end_col)


class LoaderWithLines(yaml.SafeLoader):
    def __init__(self, stream):
        yaml.SafeLoader.__init__(self, stream)
        self.add_constructor(
            "tag:yaml.org,2002:int", LoaderWithLines.construct_yaml_int
        )
        self.add_constructor(
            "tag:yaml.org,2002:str", LoaderWithLines.construct_yaml_str
        )
        self.add_constructor(
            "tag:yaml.org,2002:map", LoaderWithLines.construct_yaml_map
        )
        self.add_constructor(
            "tag:yaml.org,2002:float", LoaderWithLines.construct_yaml_float
        )

    def construct_yaml_float(self, node, *args, **kwargs):
        scalar = yaml.SafeLoader.construct_yaml_float(self, node, *args, **kwargs)
        ret = float_with_location(scalar)
        ret.location = (
            node.start_mark.line,
            node.start_mark.column,
            node.end_mark.line,
            node.end_mark.column,
        )
        return ret

    def construct_yaml_map(self, node, *args, **kwargs):
        (obj,) = yaml.SafeLoader.construct_yaml_map(self, node, *args, **kwargs)
        ret = dict_with_location(obj)
        ret.location = (
            node.start_mark.line,
            node.start_mark.column,
            node.end_mark.line,
            node.end_mark.column,
        )
        return ret

    def construct_yaml_int(self, node, *args, **kwargs):
        scalar = yaml.SafeLoader.construct_yaml_int(self, node, *args, **kwargs)
        ret = int_with_location(scalar)
        ret.location = (
            node.start_mark.line,
            node.start_mark.column,
            node.end_mark.line,
            node.end_mark.column,
        )
        return ret

    def construct_yaml_str(self, node, *args, **kwargs):
        scalar = yaml.SafeLoader.construct_scalar(self, node, *args, **kwargs)
        ret = str_with_location(scalar)
        ret.location = (
            node.start_mark.line,
            node.start_mark.column,
            node.end_mark.line,
            node.end_mark.column,
        )
        return ret


class _Position:
    def __init__(self, line: int = 0, character: int = 0):
        self.line: int = line
        self.character: int = character

    def to_dict(self):
        return {"line": self.line, "character": self.character}

    def __repr__(self):
        import json

        return json.dumps(self.to_dict(), indent=4)

    def __getitem__(self, name):
        # provide tuple-access, not just dict access.
        if name == 0:
            return self.line
        if name == 1:
            return self.character
        return getattr(self, name)

    def __eq__(self, other):
        return (
            isinstance(other, _Position)
            and self.line == other.line
            and self.character == other.character
        )

    def __ge__(self, other):
        line_gt = self.line > other.line

        if line_gt:
            return line_gt

        if self.line == other.line:
            return self.character >= other.character

        return False

    def __gt__(self, other):
        line_gt = self.line > other.line

        if line_gt:
            return line_gt

        if self.line == other.line:
            return self.character > other.character

        return False

    def __le__(self, other):
        line_lt = self.line < other.line

        if line_lt:
            return line_lt

        if self.line == other.line:
            return self.character <= other.character

        return False

    def __lt__(self, other):
        line_lt = self.line < other.line

        if line_lt:
            return line_lt

        if self.line == other.line:
            return self.character < other.character

        return False

    def __ne__(self, other):
        return not self.__eq__(other)


def is_inside(range_dct: _RangeTypedDict, line: int, col: int) -> bool:
    start = range_dct["start"]
    end = range_dct["end"]
    start_pos = _Position(start["line"], start["character"])
    end_pos = _Position(end["line"], end["character"])
    curr_pos = _Position(line, col)
    return start_pos <= curr_pos <= end_pos
