"""Nodes in the AST which represent statements or declarations."""

import musicode.musictypes as musictypes

import musicode.tree.decl_nodes as decl_nodes
from musicode.musictypes import (ArrayMusicType)
from musicode.errors import CompilerError
from musicode.il_gen import ILValue
from musicode.tree.utils import DirectLValue, report_err
from musicode.music import music

class Node:
    """Base class for representing a single node in the AST.

    All AST nodes inherit from this class.
    """

    def __init__(self):
        """Initialize node."""

        # Set range to None because it will be set by the parser.
        self.r = None

    def make_il(self, il_code, symbol_table, c):

        raise NotImplementedError


class Root(Node):
    """Root node of the program."""

    def __init__(self, nodes):
        """Initialize node."""
        super().__init__()
        self.nodes = nodes

    def make_il(self, il_code, symbol_table, c):
        """Make code for the root."""
        for node in self.nodes:
            with report_err():
                c = c.set_global(True)
                node.make_il(il_code, symbol_table, c)


class Compound(Node):
    """Node for a compound statement."""

    def __init__(self, items):
        """Initialize node."""
        super().__init__()
        self.items = items

    def make_il(self, il_code, symbol_table, c, no_scope=False):

        if not no_scope:
            symbol_table.new_scope()

        c = c.set_global(False)
        for item in self.items:
            with report_err():
                item.make_il(il_code, symbol_table, c)

        if not no_scope:
            symbol_table.end_scope()




class EmptyStatement(Node):
    """Node for a statement which is just a semicolon."""

    def __init__(self):
        """Initialize node."""
        super().__init__()

    def make_il(self, il_code, symbol_table, c):
        """Nothing to do for a blank statement."""
        pass


class ExprStatement(Node):
    """Node for a statement which contains one expression."""

    def __init__(self, expr):
        """Initialize node."""
        super().__init__()
        self.expr = expr

    def make_il(self, il_code, symbol_table, c):
        """Make code for this expression, and ignore the resulting ILValue."""
        self.expr.make_il(il_code, symbol_table, c)




class DeclInfo:



    def __init__(self, identifier, musictype, range,
                 init=None, param_names=None):
        self.identifier = identifier
        self.musictype = musictype
        self.range = range
        self.init = init
        self.param_names = param_names

    def process(self, il_code, symbol_table, c):

        if not self.identifier:
            err = "missing identifier name in declaration"
            raise CompilerError(err, self.range)


        defined = self.get_defined(symbol_table, c)

        var = symbol_table.add_variable(
            self.identifier,
            self.musictype,
            defined)

        if self.init:
            self.do_init(var, il_code, symbol_table, c)
        elif isinstance(self.musictype, ArrayMusicType):
            if var.musictype.el == musictypes.chord:
                var.py_value = [music.chord([]) for _ in range(var.musictype.n)]
            elif var.musictype.el == musictypes.note:
                var.py_value = [music.note('C') for _ in range(var.musictype.n)]

    def do_init(self, var, il_code, symbol_table, c):


        init = self.init.make_il(il_code, symbol_table, c)

        lval = DirectLValue(var)
        lval.set_to(init, il_code, self.identifier.r)

    def get_defined(self, symbol_table, c):
        """Determine whether this is a definition."""
        if (c.is_global and self.musictype.is_object() and not self.init):
            return symbol_table.TENTATIVE
        elif not (self.init):
            return symbol_table.UNDEFINED
        else:
            return symbol_table.DEFINED



class Declaration(Node):


    def __init__(self, node):
        """Initialize node."""
        super().__init__()
        self.node = node


    def make_il(self, il_code, symbol_table, c):
        """Make code for this declaration."""

        self.set_self_vars(il_code, symbol_table, c)
        decl_infos = self.get_decl_infos(self.node)
        for info in decl_infos:
            with report_err():
                info.process(il_code, symbol_table, c)

    def set_self_vars(self, il_code, symbol_table, c):

        self.il_code = il_code
        self.symbol_table = symbol_table
        self.c = c

    def get_decl_infos(self, node):
        """Given a node, returns a list of decl_info objects for that node."""

        base_type = self.make_specs_musictype(node.specs)

        out = []
        for decl, init in zip(node.decls, node.inits):
            with report_err():
                musictype, identifier = self.make_musictype(decl, base_type)

                param_identifiers = []

                out.append(DeclInfo(
                    identifier, musictype, decl.r, init,
                    param_identifiers))

        return out

    def make_musictype(self, decl, prev_ctype):

        if isinstance(decl, decl_nodes.Array):
            new_musictype = self._generate_array_musictype(decl, prev_ctype)
        elif isinstance(decl, decl_nodes.Identifier):
            return prev_ctype, decl.identifier

        return self.make_musictype(decl.child, new_musictype)

    def _generate_array_musictype(self, decl, prev_ctype):
        """Generate a function ctype from a given a decl_node."""

        if decl.n:
            il_value = decl.n.make_il(self.il_code, self.symbol_table, self.c)
            if not il_value.musictype.is_integral():
                err = "array size must have integral type"
                raise CompilerError(err, decl.r)
            if not il_value.literal:
                err = "array size must be compile-time constant"
                raise CompilerError(err, decl.r)
            if il_value.literal.val <= 0:
                err = "array size must be positive"
                raise CompilerError(err, decl.r)

            return ArrayMusicType(prev_ctype, il_value.literal.val)
        else:
            return ArrayMusicType(prev_ctype, None)


    def make_specs_musictype(self, specs):

        spec_range = specs[0].r + specs[-1].r


        base_type = self.get_base_musictype(specs, spec_range)

        return base_type

    def get_base_musictype(self, specs, spec_range):
        """Return a base ctype given a list of specs."""

        base_specs = set(musictypes.simple_types)

        our_base_specs = [str(spec.kind) for spec in specs
                          if spec.kind in base_specs]
        specs_str = " ".join(sorted(our_base_specs))

        specs = {
            "note": musictypes.note,
            "chord": musictypes.chord,
            "piece": musictypes.piece,
            "setting": musictypes.setting
        }

        if specs_str in specs:
            return specs[specs_str]

        # TODO: provide more helpful feedback on what is wrong
        descrip = "unrecognized set of type specifiers"
        raise CompilerError(descrip, spec_range)



