"""Nodes in the AST which represent expression values."""

import musicode.musictypes as musictypes
import musicode.tree.nodes as nodes

from musicode.musictypes import ArrayMusicType
from musicode.errors import CompilerError
from musicode.il_gen import ILValue
from musicode.tree.nodes import Declaration
from musicode.tree.utils import (DirectLValue,
                               set_type, report_err)
from musicode.music import music


class _ExprNode(nodes.Node):
    """Base class for representing expression nodes in the AST.

    There are two types of expression nodes, RExprNode and LExprNode.
    An expression node which can be used as an lvalue (that is, an expression
    node which can be the argument of an address-of operator) derives from
    LExprNode. Expression nodes which cannot be used as lvalues derive from
    RExprNode.
    """
    def __init__(self):
        """Initialize this ExprNode."""
        super().__init__()

    def make_il(self, il_code, symbol_table, c):
        """Generate IL code for this node and returns ILValue.

        Note that a RExprNode-derived node can never return an ILValue of
        function or array type because these must decay to addresses,
        and because an RExprNode does not represent an lvalue, no address
        can exist.

        il_code - ILCode object to add generated code to.
        symbol_table - Symbol table for current node.
        c - Context for current node, as above. This function should not
        modify this object.
        return - An ILValue representing the result of this computation.
        """
        raise NotImplementedError

    def make_il_raw(self, il_code, symbol_table, c):
        """As above, but do not decay the result."""
        raise NotImplementedError

    def lvalue(self, il_code, symbol_table, c):
        """Return the LValue representing this node.

        If this node has no LValue representation, return None.
        """
        raise NotImplementedError


class _RExprNode(nodes.Node):
    """Base class for representing an rvalue expression node in the AST.

    An RExprNode-derived node implements only the _make_il function.
    """
    def __init__(self):  # noqa D102
        nodes.Node.__init__(self)
        self._cache_raw_ilvalue = None

    def make_il(self, il_code, symbol_table, c):  # noqa D102
        raise NotImplementedError

    def make_il_raw(self, il_code, symbol_table, c):  # noqa D102
        return self.make_il(il_code, symbol_table, c)

    def lvalue(self, il_code, symbol_table, c):  # noqa D102
        return None


class _LExprNode(nodes.Node): # 左值：在内存中有明确的地址
    """Base class for representing an lvalue expression node in the AST.

    An LExprNode-derived node implements only the _lvalue function. This
    function returns an LValue object representing this node. The
    implementation of this class automatically sets up the appropriate
    make_il function which calls the lvalue implementation.

    Note that calling both make_il and make_il_raw for a single node may
    generate unnecessary or repeated code!
    """

    def __init__(self):  # noqa D102
        super().__init__()
        self._cache_lvalue = None

    def make_il(self, il_code, symbol_table, c):  # noqa D102
        lvalue = self.lvalue(il_code, symbol_table, c)
        return lvalue.val(il_code) # ILValue

    def make_il_raw(self, il_code, symbol_table, c):  # noqa D102
        return self.lvalue(il_code, symbol_table, c).val(il_code)

    def lvalue(self, il_code, symbol_table, c):
        """Return an LValue object representing this node."""
        if not self._cache_lvalue:
            self._cache_lvalue = self._lvalue(il_code, symbol_table, c)
        return self._cache_lvalue

    def _lvalue(self, il_code, symbol_table, c):
        """Return an LValue object representing this node.

        Do not call this function directly, because it does not cache the
        result. Multiple calls to this function may generate multiple error
        messages or output repeated code to il_code.
        """
        raise NotImplementedError


class MultiExpr(_RExprNode):
    """Expression that is two expressions joined by comma."""

    def __init__(self, left, right, op):
        """Initialize node."""
        self.left = left
        self.right = right
        self.op = op

    def make_il(self, il_code, symbol_table, c):
        """Make code for this node."""
        self.left.make_il(il_code, symbol_table, c)
        return self.right.make_il(il_code, symbol_table, c)


class Number(_RExprNode):
    """Expression that is just a single number."""

    def __init__(self, number):
        """Initialize node."""
        super().__init__()
        self.number = number

    def make_il(self, il_code, symbol_table, c):
        """Make code for a literal number.

        This function does not actually make any code in the IL, it just
        returns a LiteralILValue that can be used in IL code by the caller.
        """
        v = int(str(self.number))

        if musictypes.int_min <= v <= musictypes.int_max:
            il_value = ILValue(musictypes.integer)
        else:
            err = "integer literal too large to be represented by any " \
                  "integer type"
            raise CompilerError(err, self.number.r)

        il_code.register_literal_var(il_value, v)
        return il_value


class String(_LExprNode):
    """Expression that is a string.

    chars (List(int)) - String this expression represents, as a null-terminated
    list of the ASCII representations of each character.

    """

    def __init__(self, chars):
        """Initialize Node."""
        super().__init__()
        self.chars = chars

    def _lvalue(self, il_code, symbol_table, c):
        il_value = ILValue(ArrayMusicType(musictypes.char, len(self.chars)))
        il_code.register_string_literal(il_value, self.chars)
        return DirectLValue(il_value)


class Identifier(_LExprNode):
    """Expression that is a single identifier."""

    def __init__(self, identifier):
        """Initialize node."""
        super().__init__()
        self.identifier = identifier

    def _lvalue(self, il_code, symbol_table, c):
        var = symbol_table.lookup_variable(self.identifier)
        return DirectLValue(var)


class ParenExpr(nodes.Node):
    """Expression in parentheses.

    This is implemented a bit hackily. Rather than being an LExprNode or
    RExprNode like all the other nodes, a paren expression can be either
    depending on what's inside. So for all function calls to this function,
    we simply dispatch to the expression inside.
    """

    def __init__(self, expr):
        """Initialize node."""
        super().__init__()
        self.expr = expr

    def lvalue(self, il_code, symbol_table, c):
        """Return lvalue of this expression."""
        return self.expr.lvalue(il_code, symbol_table, c)

    def make_il(self, il_code, symbol_table, c):
        """Make IL code for this expression."""
        return self.expr.make_il(il_code, symbol_table, c)

    def make_il_raw(self, il_code, symbol_table, c):
        """Make raw IL code for this expression."""
        return self.expr.make_il_raw(il_code, symbol_table, c)


class _ArithBinOp(_RExprNode):
    """Base class for some binary operators.

    Binary operators like +, -, ==, etc. are similar in many respects. They
    convert their arithmetic arguments, etc. This is a base class for
    nodes of those types of operators.
    """

    def __init__(self, left, right, op):
        """Initialize node."""
        super().__init__()
        self.left = left
        self.right = right
        self.op = op

    def make_il(self, il_code, symbol_table, c):
        """Make code for this node."""

        left = self.left.make_il(il_code, symbol_table, c)
        right = self.right.make_il(il_code, symbol_table, c)


        return self._arith(left, right, il_code)


    def _arith(self, left, right, il_code):
        """Return the result of this operation on given arithmetic operands.

        Promotions and conversions are done by caller, so the implementation of
        this function need not convert operands.

        A default implementation is provided, but this can be overriden by
        derived classes.

        left - ILValue for left operand
        right - ILValue for right operand
        """
        # out = ILValue(left.ctype)
        # # [code]
        # return out
        raise NotImplementedError

class Plus(_ArithBinOp):
    """Expression that is sum of two expressions.

    left - Expression on left side
    right - Expression on right side
    op (Token) - Plus operator token
    """

    def __init__(self, left, right, op):
        """Initialize node."""
        super().__init__(left, right, op)


    def _arith(self, left, right, il_code):
        """Make addition code if either operand is non-arithmetic type."""

        # Multiply by size of objects
        out = ILValue(musictypes.python)
        out.py_value = left.py_value + right.py_value
        return out


class Minus(_ArithBinOp):
    """Expression that is the difference of two expressions.

    left - Expression on left side
    right - Expression on right side
    op (Token) - Plus operator token
    """

    def __init__(self, left, right, op):
        """Initialize node."""
        super().__init__(left, right, op)

    def _arith(self, left, right, il_code):
        """Make addition code if either operand is non-arithmetic type."""

        # Multiply by size of objects
        out = ILValue(musictypes.python)
        out.py_value = left.py_value - right.py_value
        return out


class Mult(_ArithBinOp):
    """Expression that is product of two expressions."""

    def __init__(self, left, right, op):
        """Initialize node."""
        super().__init__(left, right, op)

    def _arith(self, left, right, il_code):
        """Make addition code if either operand is non-arithmetic type."""

        # Multiply by size of objects
        out = ILValue(musictypes.python)
        out.py_value = left.py_value * right.py_value
        return out

class Dot(_ArithBinOp):
    """Expression that is product of two expressions."""

    def __init__(self, left, right, op):
        """Initialize node."""
        super().__init__(left, right, op)

    def _arith(self, left, right, il_code):
        """Make addition code if either operand is non-arithmetic type."""

        # Multiply by size of objects
        out = ILValue(musictypes.python)
        out.py_value =  float(str(left.py_value) + '.' + str(right.py_value))
        return out

class BitOr(_ArithBinOp):
    """Expression that is product of two expressions."""

    def __init__(self, left, right, op):
        """Initialize node."""
        super().__init__(left, right, op)

    def _arith(self, left, right, il_code):
        """Make addition code if either operand is non-arithmetic type."""

        # Multiply by size of objects
        out = ILValue(musictypes.python)
        out.py_value =  left.py_value | right.py_value
        return out

class BitAnd(_ArithBinOp):
    """Expression that is product of two expressions."""

    def __init__(self, left, right, op):
        """Initialize node."""
        super().__init__(left, right, op)

    def _arith(self, left, right, il_code):
        """Make addition code if either operand is non-arithmetic type."""

        # Multiply by size of objects
        out = ILValue(musictypes.python)
        out.py_value =  left.py_value & right.py_value
        return out


class _IntBinOp(_ArithBinOp):
    """Base class for operations that works with integral type operands."""

    def __init__(self, left, right, op):
        """Initialize node."""
        super().__init__(left, right, op)


class Div(_ArithBinOp):
    """Expression that is quotient of two expressions."""

    def __init__(self, left, right, op):
        """Initialize node."""
        super().__init__(left, right, op)

    def _arith(self, left, right, il_code):
        """Make addition code if either operand is non-arithmetic type."""

        # Multiply by size of objects
        out = ILValue(musictypes.python)
        out.py_value = left.py_value / right.py_value
        return out

class Mod(_ArithBinOp):
    """Expression that is modulus of two expressions."""

    def __init__(self, left, right, op):
        """Initialize node."""
        super().__init__(left, right, op)

    def _arith(self, left, right, il_code):
        """Make addition code if either operand is non-arithmetic type."""

        # Multiply by size of objects
        out = ILValue(musictypes.python)
        out.py_value = left.py_value % right.py_value
        return out

class At(_ArithBinOp):
    """Expression that is modulus of two expressions."""

    def __init__(self, left, right, op):
        """Initialize node."""
        super().__init__(left, right, op)

    def _arith(self, left, right, il_code):
        """Make addition code if either operand is non-arithmetic type."""

        # Multiply by size of objects
        out = ILValue(musictypes.python)
        out.py_value = left.py_value @ right.py_value
        return out



class _BitShift(_ArithBinOp):
    """Represents a `<<` and `>>` bitwise shift operators.
    Each of operands must have integer type.
    """

    def __init__(self, left, right, op):
        """Initialize node."""
        super().__init__(left, right, op)

class RBitShift(_ArithBinOp):
    """Represent a `>>` operator."""
    def __init__(self, left, right, op):
        """Initialize node."""
        super().__init__(left, right, op)

    def _arith(self, left, right, il_code):
        """Make addition code if either operand is non-arithmetic type."""

        # Multiply by size of objects
        out = ILValue(musictypes.python)
        out.py_value = left.py_value >> right.py_value
        return out


class LBitShift(_ArithBinOp):
    """Represent a `<<` operator."""

    def __init__(self, left, right, op):
        """Initialize node."""
        super().__init__(left, right, op)

    def _arith(self, left, right, il_code):
        """Make addition code if either operand is non-arithmetic type."""

        # Multiply by size of objects
        out = ILValue(musictypes.python)
        out.py_value = left.py_value << right.py_value
        return out


class _Equality(_ArithBinOp):
    """Base class for == and != nodes."""

    def __init__(self, left, right, op):
        """Initialize node."""
        super().__init__(left, right, op)


class Equality(_ArithBinOp):
    """Expression that checks equality of two expressions."""

    def __init__(self, left, right, op):
        """Initialize node."""
        super().__init__(left, right, op)

    def _arith(self, left, right, il_code):
        """Make addition code if either operand is non-arithmetic type."""

        # Multiply by size of objects
        out = ILValue(musictypes.python)
        out.py_value = left.py_value == right.py_value
        return out


class Inequality(_ArithBinOp):
    """Expression that checks inequality of two expressions."""

    def __init__(self, left, right, op):
        """Initialize node."""
        super().__init__(left, right, op)

    def _arith(self, left, right, il_code):
        """Make addition code if either operand is non-arithmetic type."""

        # Multiply by size of objects
        out = ILValue(musictypes.python)
        out.py_value = left.py_value != right.py_value
        return out


class _Relational(_ArithBinOp):
    """Base class for <, <=, >, and >= nodes."""

    def __init__(self, left, right, op):
        """Initialize node."""
        super().__init__(left, right, op)


class LessThan(_ArithBinOp):
    def __init__(self, left, right, op):
        """Initialize node."""
        super().__init__(left, right, op)

    def _arith(self, left, right, il_code):
        """Make addition code if either operand is non-arithmetic type."""

        # Multiply by size of objects
        out = ILValue(musictypes.python)
        out.py_value = left.py_value < right.py_value
        return out


class GreaterThan(_ArithBinOp):
    def __init__(self, left, right, op):
        """Initialize node."""
        super().__init__(left, right, op)

    def _arith(self, left, right, il_code):
        """Make addition code if either operand is non-arithmetic type."""

        # Multiply by size of objects
        out = ILValue(musictypes.python)
        out.py_value = left.py_value > right.py_value
        return out


class LessThanOrEq(_ArithBinOp):
    def __init__(self, left, right, op):
        """Initialize node."""
        super().__init__(left, right, op)

    def _arith(self, left, right, il_code):
        """Make addition code if either operand is non-arithmetic type."""

        # Multiply by size of objects
        out = ILValue(musictypes.python)
        out.py_value = left.py_value <= right.py_value
        return out


class GreaterThanOrEq(_ArithBinOp):
    def __init__(self, left, right, op):
        """Initialize node."""
        super().__init__(left, right, op)

    def _arith(self, left, right, il_code):
        """Make addition code if either operand is non-arithmetic type."""

        # Multiply by size of objects
        out = ILValue(musictypes.python)
        out.py_value = left.py_value >= right.py_value
        return out


class Equals(_RExprNode):
    """Expression that is an assignment."""

    def __init__(self, left, right, op):
        """Initialize node."""
        super().__init__()
        self.left = left
        self.right = right
        self.op = op

    def make_il(self, il_code, symbol_table, c):
        """Make code for this node."""
        right = self.right.make_il(il_code, symbol_table, c)
        lvalue = self.left.lvalue(il_code, symbol_table, c)

        if lvalue and lvalue.modable():
            return lvalue.set_to(right, il_code, self.op.r)
        else:
            err = "expression on left of '=' is not assignable"
            raise CompilerError(err, self.left.r)


class _CompoundPlusMinus(_RExprNode):


    def __init__(self, left, right, op):
        """Initialize node."""
        super().__init__()
        self.left = left
        self.right = right
        self.op = op


class PlusEquals(_CompoundPlusMinus):
    """Expression that is +=."""

    def make_il(self, il_code, symbol_table, c):
        """Make code for this node."""
        right = self.right.make_il(il_code, symbol_table, c)
        lvalue = self.left.lvalue(il_code, symbol_table, c)
        if not lvalue or not lvalue.modable():
            err = f"expression on left of '{str(self.op)}' is not assignable"
            raise CompilerError(err, self.left.r)

        left = self.left.make_il(il_code, symbol_table, c)
        out = ILValue(musictypes.python)

        out.py_value = left.py_value + right.py_value
        lvalue.set_to(out, il_code, self.op.r)


class MinusEquals(_CompoundPlusMinus):
    """Expression that is -=."""

    def make_il(self, il_code, symbol_table, c):
        """Make code for this node."""
        right = self.right.make_il(il_code, symbol_table, c)
        lvalue = self.left.lvalue(il_code, symbol_table, c)
        if not lvalue or not lvalue.modable():
            err = f"expression on left of '{str(self.op)}' is not assignable"
            raise CompilerError(err, self.left.r)

        left = self.left.make_il(il_code, symbol_table, c)
        out = ILValue(musictypes.python)

        out.py_value = left.py_value - right.py_value
        lvalue.set_to(out, il_code, self.op.r)


class StarEquals(_CompoundPlusMinus):
    """Expression that is *=."""

    def make_il(self, il_code, symbol_table, c):
        """Make code for this node."""
        right = self.right.make_il(il_code, symbol_table, c)
        lvalue = self.left.lvalue(il_code, symbol_table, c)
        if not lvalue or not lvalue.modable():
            err = f"expression on left of '{str(self.op)}' is not assignable"
            raise CompilerError(err, self.left.r)

        left = self.left.make_il(il_code, symbol_table, c)
        out = ILValue(musictypes.python)

        out.py_value = left.py_value * right.py_value
        lvalue.set_to(out, il_code, self.op.r)


class DivEquals(_CompoundPlusMinus):
    """Expression that is /=."""

    def make_il(self, il_code, symbol_table, c):
        """Make code for this node."""
        right = self.right.make_il(il_code, symbol_table, c)
        lvalue = self.left.lvalue(il_code, symbol_table, c)
        if not lvalue or not lvalue.modable():
            err = f"expression on left of '{str(self.op)}' is not assignable"
            raise CompilerError(err, self.left.r)

        left = self.left.make_il(il_code, symbol_table, c)
        out = ILValue(musictypes.python)

        out.py_value = left.py_value / right.py_value
        lvalue.set_to(out, il_code, self.op.r)


class ModEquals(_CompoundPlusMinus):
    """Expression that is %=."""

    def make_il(self, il_code, symbol_table, c):
        """Make code for this node."""
        right = self.right.make_il(il_code, symbol_table, c)
        lvalue = self.left.lvalue(il_code, symbol_table, c)
        if not lvalue or not lvalue.modable():
            err = f"expression on left of '{str(self.op)}' is not assignable"
            raise CompilerError(err, self.left.r)

        left = self.left.make_il(il_code, symbol_table, c)
        out = ILValue(musictypes.python)

        out.py_value = left.py_value % right.py_value
        lvalue.set_to(out, il_code, self.op.r)


class _IncrDecr(_RExprNode):
    """Base class for prefix/postfix increment/decrement operators."""

    def __init__(self, expr):
        """Initialize node."""
        super().__init__()
        self.expr = expr


class PreIncr(_IncrDecr):
    """Prefix increment."""

    descrip = "increment"
    return_new = True

    def make_il(self, il_code, symbol_table, c):
        """Make code for this node."""
        lval = self.expr.lvalue(il_code, symbol_table, c)

        if not lval or not lval.modable():
            err = f"operand of {self.descrip} operator not a modifiable lvalue"
            raise CompilerError(err, self.expr.r)

        val = self.expr.make_il(il_code, symbol_table, c)

        new_val = ILValue(musictypes.python)

        if self.return_new:
            new_val.py_value = val.py_value + 1
            lval.set_to(new_val, il_code, self.expr.r)
            return new_val
        else:
            old_val = ILValue(musictypes.python)
            old_val.py_value = val.py_value
            new_val.py_value = val.py_value + 1
            lval.set_to(new_val, il_code, self.expr.r)
            return old_val


class PostIncr(_IncrDecr):
    """Postfix increment."""

    descrip = "increment"
    return_new = False

    def make_il(self, il_code, symbol_table, c):
        """Make code for this node."""
        lval = self.expr.lvalue(il_code, symbol_table, c)

        if not lval or not lval.modable():
            err = f"operand of {self.descrip} operator not a modifiable lvalue"
            raise CompilerError(err, self.expr.r)

        val = self.expr.make_il(il_code, symbol_table, c)

        new_val = ILValue(musictypes.python)

        if self.return_new:
            new_val.py_value = val.py_value + 1
            lval.set_to(new_val, il_code, self.expr.r)
            return new_val
        else:
            old_val = ILValue(musictypes.python)
            old_val.py_value = val.py_value
            new_val.py_value = val.py_value + 1
            lval.set_to(new_val, il_code, self.expr.r)
            return old_val


class PreDecr(_IncrDecr):
    """Prefix decrement."""

    descrip = "decrement"
    return_new = True


    def make_il(self, il_code, symbol_table, c):
        """Make code for this node."""
        lval = self.expr.lvalue(il_code, symbol_table, c)

        if not lval or not lval.modable():
            err = f"operand of {self.descrip} operator not a modifiable lvalue"
            raise CompilerError(err, self.expr.r)

        val = self.expr.make_il(il_code, symbol_table, c)

        new_val = ILValue(musictypes.python)

        if self.return_new:
            new_val.py_value = val.py_value - 1
            lval.set_to(new_val, il_code, self.expr.r)
            return new_val
        else:
            old_val = ILValue(musictypes.python)
            old_val.py_value = val.py_value
            new_val.py_value = val.py_value - 1
            lval.set_to(new_val, il_code, self.expr.r)
            return old_val


class PostDecr(_IncrDecr):
    """Postfix decrement."""

    descrip = "decrement"
    return_new = False

    def make_il(self, il_code, symbol_table, c):
        """Make code for this node."""
        lval = self.expr.lvalue(il_code, symbol_table, c)

        if not lval or not lval.modable():
            err = f"operand of {self.descrip} operator not a modifiable lvalue"
            raise CompilerError(err, self.expr.r)

        val = self.expr.make_il(il_code, symbol_table, c)

        new_val = ILValue(musictypes.python)

        if self.return_new:
            new_val.py_value = val.py_value - 1
            lval.set_to(new_val, il_code, self.expr.r)
            return new_val
        else:
            old_val = ILValue(musictypes.python)
            old_val.py_value = val.py_value
            new_val.py_value = val.py_value - 1
            lval.set_to(new_val, il_code, self.expr.r)
            return old_val


class _ArithUnOp(_RExprNode):
    """Base class for unary plus, minus, and bit-complement."""

    descrip = None
    opnd_descrip = "arithmetic"

    def __init__(self, expr):
        """Initialize node."""
        super().__init__()
        self.expr = expr


class UnaryPlus(_ArithUnOp):
    """Positive."""

    descrip = "unary plus"

    def make_il(self, il_code, symbol_table, c):
        """Make code for this node."""
        expr = self.expr.make_il(il_code, symbol_table, c)

        out = ILValue(musictypes.python)
        # perform constant folding
        out.py_value = +expr.py_value
        return out



class UnaryMinus(_ArithUnOp):
    """Negative."""

    descrip = "unary minus"

    def make_il(self, il_code, symbol_table, c):
        """Make code for this node."""
        expr = self.expr.make_il(il_code, symbol_table, c)

        out = ILValue(musictypes.python)
        # perform constant folding
        out.py_value = -expr.py_value
        return out


class Compl(_ArithUnOp):
    """Logical bitwise negative."""

    descrip = "bit-complement"
    opnd_descrip = "integral"

    def make_il(self, il_code, symbol_table, c):
        """Make code for this node."""
        expr = self.expr.make_il(il_code, symbol_table, c)

        out = ILValue(musictypes.python)
        # perform constant folding
        out.py_value = ~expr.py_value
        return out



class ArraySubsc(_LExprNode):
    """Array subscript."""

    def __init__(self, head, arg):
        """Initialize node."""
        super().__init__()
        self.head = head
        self.arg = arg

    def _lvalue(self, il_code, symbol_table, c):
        """Return lvalue form of this node.

        We have two main cases here. The first case covers most simple
        situations, like `array[5]` or `array[x+3]`, and the second case
        covers more complex situations like `array[4][2]` or an array
        within a struct.

        In the first case, one of the two operands is a DirectLValue array
        (i.e. just a variable, not a lookup into another object). This
        means it will have a spot in memory assigned to it by the register
        allocator, and we can return a RelativeLValue object from this
        function. This case corresponds to `matched` being True. A
        RelativeLValue object usually becomes an assembly command like
        `[rbp-40+3*rax]`, which is more efficient than manually computing
        the address like happens in the second case.

        In the second case, neither operand is a DirectLValue array. This is
        the case for two-dimensional arrays, for example. Here, we proceed
        naively and get the address for the pointer side. This is a little
        bit less efficient. Ideally, in cases like `array[2][4]` where the
        lookup address could be computed at compile-time, we'd be able to do
        that, but this is not yet supported (TODO).

        """

        # One operand should be pointer to complete object type, and the
        # other should be any integer type.

        head_lv = self.head.lvalue(il_code, symbol_table, c)
        arg_lv = self.arg.lvalue(il_code, symbol_table, c)

        head_v = head_lv.il_value
        arg_v = arg_lv.il_value

        out = ILValue(musictypes.python)
        # perform constant folding
        out.py_value = head_v[arg_v]
        return DirectLValue(out)



class PlayExpr(_RExprNode):
    """Node representing sizeof with expression operand.

    expr (_ExprNode) - the expression to get the size of
    """
    def __init__(self, expr):
        super().__init__()
        self.expr = expr

    def make_il(self, il_code, symbol_table, c):
        """Return a compile-time integer literal as the expression size."""

        dummy_il_code = il_code.copy()
        expr = self.expr.make_il_raw(dummy_il_code, symbol_table, c)
        music.play(expr.py_value)
        return expr


class ScoreExpr(_RExprNode):
    """Node representing sizeof with expression operand.

    expr (_ExprNode) - the expression to get the size of
    """
    def __init__(self, expr):
        super().__init__()
        self.expr = expr

    def make_il(self, il_code, symbol_table, c):
        """Return a compile-time integer literal as the expression size."""

        dummy_il_code = il_code.copy()
        expr = self.expr.make_il_raw(dummy_il_code, symbol_table, c)
        music.gen_score(expr.py_value)
        return expr



class Args(_RExprNode):
    """Function call.

    args - List of expressions for each argument
    """
    def __init__(self, args):
        """Initialize node."""
        super().__init__()
        self.args = args

    def make_il(self, il_code, symbol_table, c):
        """Make code for this node."""


        final_args = self._get_args(
            il_code, symbol_table, c)


        ret = ILValue(musictypes.python)
        v = [arg.py_value for arg in final_args]
        il_code.register_music_literal(ret, v)
        return ret

    def _get_args(self, il_code, symbol_table, c):
        """Return list of argument ILValues for function this represents.

        Use _get_args_without_prototype when the function this represents
        has no prototype. This function only performs integer promotion on the
        arguments before passing them to the called function.
        """
        final_args = []
        for arg_given in self.args:
            arg = arg_given.make_il(il_code, symbol_table, c)
            final_args.append(arg)
        return final_args





