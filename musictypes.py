import copy

import musicode.token_kinds as token_kinds

class MusicType:
    """
    Represents a Music type, like `note` or `chord`.
    """


    def __init__(self):
        # Required for super hacky struct trick, see the weak_compat
        # function for the struct.
        self._orig = self


    def is_arith(self):
        """Check whether this is an arithmetic type."""
        return False

    def is_integral(self):
        """Check whether this is an integral type."""
        return False

    def is_array(self):
        """Check whether this is an array type."""
        return False

    def is_object(self):
        """Check if this is an object type."""
        return False

    def compatible(self, other):
        """Check whether given `other` C type is compatible with self."""
        return self.weak_compat(other)

    def weak_compat(self, other):
        """Check for weak compatibility with `other` ctype.

        Two types are "weakly compatible" if their unqualified version are
        compatible.
        """
        raise NotImplementedError




class IntegerCType(MusicType):
    """Represents an integer C type, like 'unsigned long' or 'bool'.

    This class must be instantiated only once for each distinct integer C type.

    size (int) - The result of sizeof on this type.
    signed (bool) - Whether this type is signed.

    """

    def __init__(self):
        """Initialize type."""
        super().__init__()


    def is_arith(self):
        """Check whether this is an arithmetic type."""
        return True

    def is_integral(self):
        """Check whether this is an integral type."""
        return True

    def is_object(self):
        """Check if this is an object type."""
        return True

    def weak_compat(self, other):
        """Check whether two types are compatible."""

        # TODO: _orig stuff is hacky...
        # Find a more reliable way to talk about types being equal.
        return other._orig == self._orig



class NoteMusicType(MusicType):
    def __init__(self):
        """Initialize type."""
        super().__init__()

    def is_object(self):
        """Check if this is an object type."""
        return True

    def weak_compat(self, other):
        """Check whether two types are compatible."""

        # TODO: _orig stuff is hacky...
        # Find a more reliable way to talk about types being equal.
        return other._orig == self._orig

class ChordMusicType(MusicType):
    def __init__(self):
        """Initialize type."""
        super().__init__()

    def is_object(self):
        """Check if this is an object type."""
        return True

    def weak_compat(self, other):
        """Check whether two types are compatible."""

        # TODO: _orig stuff is hacky...
        # Find a more reliable way to talk about types being equal.
        return other._orig == self._orig

class PieceMusicType(MusicType):
    def __init__(self):
        """Initialize type."""
        super().__init__()

    def is_object(self):
        """Check if this is an object type."""
        return True

    def weak_compat(self, other):
        """Check whether two types are compatible."""

        # TODO: _orig stuff is hacky...
        # Find a more reliable way to talk about types being equal.
        return other._orig == self._orig

class SettingMusicType(MusicType):
    def __init__(self):
        """Initialize type."""
        super().__init__()

    def is_object(self):
        """Check if this is an object type."""
        return True

    def weak_compat(self, other):
        """Check whether two types are compatible."""

        # TODO: _orig stuff is hacky...
        # Find a more reliable way to talk about types being equal.
        return other._orig == self._orig

class PythonType(MusicType):
    def __init__(self):
        """Initialize type."""
        super().__init__()

    def is_object(self):
        """Check if this is an object type."""
        return True

    def weak_compat(self, other):
        """Check whether two types are compatible."""

        # TODO: _orig stuff is hacky...
        # Find a more reliable way to talk about types being equal.
        return other._orig == self._orig

class ArrayMusicType(MusicType):
    """Represents an array Music type.

    el (MusicType) - Type of each element in array.
    n (int) - Size of array (or None if this is incomplete)

    """

    def __init__(self, el, n):
        """Initialize type."""
        self.el = el
        self.n = n
        super().__init__()

    def is_array(self):
        """Check whether this is an array type."""
        return True

    def is_object(self):
        """Check if this is an object type."""
        return True

    def compatible(self, other):
        """Return True iff other is a compatible type to self."""
        return (other.is_array() and self.el.compatible(other.el) and
                (self.n is None or other.n is None or self.n == other.n))

note = NoteMusicType()
chord = ChordMusicType()
piece = PieceMusicType()
setting = SettingMusicType()

integer = IntegerCType()
char = IntegerCType()
python = PythonType()

int_max = 2147483647
int_min = -2147483648

simple_types = {
    token_kinds.note_kw: note,
    token_kinds.chord_kw: chord,
    token_kinds.piece_kw: piece,
    token_kinds.setting_kw: setting
}
