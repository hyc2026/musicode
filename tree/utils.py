"""Utility objects for the AST nodes and IL generation steps of ShivyC."""

from contextlib import contextmanager

from musicode.errors import CompilerError, error_collector
from musicode.il_gen import ILValue


class LValue:
    """Represents an LValue."""

    def musictype(self):
        """Return the musictype that is stored by this LValue.

        For example, if this LValue represents a dereferenced pointer to an
        integer, then this function returns a ctype of integer.
        """
        raise NotImplementedError

    def set_to(self, rvalue, il_code, r):
        """Emit code to set the given lvalue to the given ILValue.

        rvalue (ILValue) - rvalue to set this lvalue to
        il_code (ILCode) - ILCode object to add generated code
        r (Range) - Range for warning/error messages
        return - ILValue representing the result of this operation

        """
        raise NotImplementedError

    def addr(self, il_code):
        """Generate code for and return address of this lvalue."""
        raise NotImplementedError

    def val(self, il_code):
        """Generate code for and return the value currently stored."""
        raise NotImplementedError

    def modable(self):
        """Return whether this is a modifiable lvalue."""

        musictype = self.musictype()
        if musictype.is_array():
            return False

        return True


class DirectLValue(LValue):
    """Represents a direct LValue.

    A direct LValue stores an ILValue to which this LValue refers. For
    example, a variable is a direct LValue.
    """
    def __init__(self, il_value):
        """Initialize DirectLValue with the IL value it represents."""
        self.il_value = il_value

    def musictype(self):  # noqa D102
        return self.il_value.musictype

    def set_to(self, rvalue, il_code, r):  # noqa D102 # TODO：还是在声明的那部分初始化？
        return set_type(rvalue, self.musictype(), il_code, self.il_value)

    def val(self, il_code):  # noqa D102
        return self.il_value


@contextmanager
def report_err():
    """Catch and add any errors to error collector."""
    try:
        yield
    except CompilerError as e:
        error_collector.add(e)



def set_type(il_value, musictype, il_code, output=None):
    """If necessary, emit code to cast given il_value to the given ctype.

    If `output` is given, then this function expects output.ctype to be the
    same as ctype, sets `output` to the casted value, and returns output.

    If `output` is not given, this function returns an IL value with type
    ctype. If `il_value.ctype` matches given ctype, this function may return
    `il_value` directly. So, the return value should never have its value
    changed because this may affect the value in the given `il_value`.

    This function does no type checking and will never produce a warning or
    error.
    """
    if not output and il_value.musictype.compatible(musictype):
        return il_value
    elif output == il_value:
        return il_value
    elif not output and il_value.literal: # 相当于是给原来的ilvaue换了个type？
        output = ILValue(musictype)
        val = il_value.literal.val
        il_code.register_literal_var(output, val)
        return output
    else:
        if not output:
            output = ILValue(musictype)
        # il_code.add(value_cmds.Set(output, il_value))
        il_code.set_py_value(output, il_value)
        return output





