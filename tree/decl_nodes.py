

class DeclNode:
    """Base class for all decl_nodes nodes."""

    pass


class Root(DeclNode):


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





