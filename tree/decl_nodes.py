"""Classes for the nodes that form the declaration and type name tree.

This tree/node system is pretty distinct from the tree/node system used for
the rest of the AST because parsing declarations is very different from
parsing other parts of the language due to the "backwards"-ness of C
declaration syntax, as described below:

The declaration trees produces by the parser feel "backwards". For example,
the following:

    int *arr[3];

parses to:

    Root([token_kinds.int_kw], [Pointer(Array(3, Identifier(tok)))])

while the following:

    int (*arr)[3];

parses to:

    Root([token_kinds.int_kw], [Array(3, Pointer(Identifier(tok)))])

Declaration trees are to be read inside-out. So, the first example above is
an array of 3 pointers to int, and the second example is a pointer to an
array of 3 integers. The DeclarationNode class in tree.py performs the task
of reversing these trees when forming the ctype.

"""

import musicode.token_kinds as token_kinds


class DeclNode:
    """Base class for all decl_nodes nodes."""

    pass


class Root(DeclNode):
    """Represents a list of declaration specifiers and declarators.

    specs (List(Tokens/Nodes)) - list of the declaration specifiers, as tokens
    decls (List(Node)) - list of declarator nodes
    """

    def __init__(self, specs, decls, inits=None):
        """Generate root node."""
        self.specs = specs
        self.decls = decls

        if inits:
            self.inits = inits
        else:
            self.inits = [None] * len(self.decls)

        super().__init__()


class Array(DeclNode):
    """Represents an array of a type.

    n (int) - size of the array

    """

    def __init__(self, n, child):
        """Generate array node."""
        self.n = n # expr.nodes
        self.child = child # Identifier 数组名
        super().__init__()




class Identifier(DeclNode):
    """Represents an identifier.

    If this is a type name and has no identifier, `identifier` is None.
    """

    def __init__(self, identifier):
        """Generate identifier node from an identifier token."""
        self.identifier = identifier
        super().__init__()





