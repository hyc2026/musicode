"""Objects used for the AST -> IL phase of the compiler."""

from collections import namedtuple
from copy import copy

from musicode.musictypes import MusicType
import musicode.musictypes as musictypes
from musicode.errors import CompilerError
from musicode.music import music
from collections import Iterable

class ILCode:

    def __init__(self):
        """Initialize IL code."""
        self.commands = {}
        self.cur_func = None

        self.literals = {}
        self.string_literals = {}
        self.music_literals = {}


    def copy(self):

        new = ILCode()
        new.commands = {name: self.commands[name].copy()
                        for name in self.commands}
        new.cur_func = self.cur_func
        self.literals = self.literals.copy()
        self.string_literals = self.string_literals.copy()
        self.music_literals = self.music_literals.copy()

        return new

    def start_func(self, func):

        self.cur_func = func
        self.commands[func] = []

    def add(self, command):

        self.commands[self.cur_func].append(command)


    def register_literal_var(self, il_value, value):

        il_value.literal = IntegerLiteral(value)
        il_value.py_value = il_value.literal.val
        self.literals[il_value] = value

    def register_string_literal(self, il_value, chars):

        il_value.literal = StringLiteral(chars)
        il_value.py_value = ''.join(chr(c) for c in il_value.literal.val)[:-1]
        self.string_literals[il_value] = chars

    def register_music_literal(self, il_value, value):

        il_value.literal = MusicLiteral(value)
        il_value.py_value = il_value.literal.val
        self.music_literals[il_value] = value

    def set_py_value(self, il_value_dst, il_value_src):


        if il_value_dst.musictype == musictypes.piece:
            il_value_dst.py_value = music.piece(*il_value_src.py_value)
            for track in il_value_dst.py_value.tracks:
                print(track.details())
        else:
            if il_value_src.literal:
                if isinstance(il_value_src.py_value, list):
                    if il_value_dst.musictype == musictypes.note:
                        il_value_dst.py_value = music.note(*il_value_src.py_value)
                    elif il_value_dst.musictype == musictypes.chord:
                        il_value_dst.py_value = music.chord(il_value_src.py_value)
                    else:
                        il_value_dst.py_value = il_value_src.py_value
                else:
                    if il_value_dst.musictype == musictypes.note:
                        il_value_dst.py_value = music.toNote(il_value_src.py_value)
                    elif il_value_dst.musictype == musictypes.chord:
                        il_value_dst.py_value = music.trans(il_value_src.py_value)

            else:
                il_value_dst.py_value = il_value_src.py_value # 赋值




class ILValue:
    """Value that appears as an element in generated IL code.

    ctype (CType) - C type of this value.
    literal_val - the value of this IL value if it represents a literal
    value. Do not set this value directly; it is set by the
    ILCode.register_literal_var function.
    """

    def __init__(self, musictype):
        """Initialize IL value."""
        self.musictype = musictype
        self.literal = None
        self.py_value = None

    def __str__(self):  # pragma: no cover
        return f'{id(self) % 1000:03}'

    def __repr__(self):  # pragma: no cover
        return str(self)


class _Literal:
    """Base class for integer literals, string literals, etc."""
    def __init__(self, val):
        self.val = val


class IntegerLiteral(_Literal):
    """Class for integer literals."""
    def __init__(self, val):
        super().__init__(int(val))


class StringLiteral(_Literal):
    """Class for string literals."""
    def __init__(self, val):
        # super().__init__(str(val))
        super().__init__(val)

class MusicLiteral(_Literal):
    """Class for music literals."""
    def __init__(self, val):
        super().__init__(val)


class SymbolTable:
    """Symbol table for the IL -> AST phase.

    This object stores variable names, types, typedefs, and maintains
    information on the variable linkages and storage durations.
    """
    Tables = namedtuple('Tables', ['vars', 'structs'])

    # Definition statuses
    UNDEFINED = 1
    TENTATIVE = 2
    DEFINED = 3

    def __init__(self):

        self.tables = []
        self.def_state = {}


        # Store the names of all IL values.
        # ILValue -> name
        self.names = {}

        self.new_scope()

    def new_scope(self):
        """Initialize a new scope for the symbol table."""
        self.tables.append(self.Tables(dict(), dict()))

    def end_scope(self):
        """End the most recently started scope."""
        self.tables.pop()

    def _lookup_raw(self, name):

        for table, _ in self.tables[::-1]:
            if name in table:
                return table[name]

    def lookup_variable(self, identifier):

        ret = self._lookup_raw(identifier.content)

        if ret and isinstance(ret, ILValue):
            return ret
        else:
            descrip = f"use of undeclared identifier '{identifier.content}'"
            raise CompilerError(descrip, identifier.r)


    def add_variable(self, identifier, musictype, defined):

        name = identifier.content

        # if it's already declared in this scope
        if name in self.tables[-1].vars:
            var = self.tables[-1].vars[name]
            if isinstance(var, MusicType):
                err = f"redeclared type definition '{name}' as variable"
                raise CompilerError(err, identifier.r)
        else:
            var = ILValue(musictype)


        self.tables[-1].vars[name] = var


        self.def_state[var] = max(self.def_state.get(var, 0), defined)


        self.names[var] = name
        return var


class Context:

    def __init__(self):
        """Initialize Context."""
        self.break_label = None
        self.continue_label = None
        self.return_type = None
        self.is_global = False

    def set_global(self, val):
        """Return copy of self with is_global set to given value."""
        c = copy(self)
        c.is_global = val
        return c

    def set_break(self, lab):
        """Return copy of self with break_label set to given value."""
        c = copy(self)
        c.break_label = lab
        return c

    def set_continue(self, lab):
        """Return copy of self with break_label set to given value."""
        c = copy(self)
        c.continue_label = lab
        return c

    def set_return(self, ctype):
        """Return copy of self with return_type set to given value."""
        c = copy(self)
        c.return_type = ctype
        return c
