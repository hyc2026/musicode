
class TokenKind:

    def __init__(self, text_repr="", kinds=[]):

        self.text_repr = text_repr
        kinds.append(self)
        kinds.sort(key=lambda kind: -len(kind.text_repr))

    def __str__(self):
        """Return the representation of this token kind."""
        return self.text_repr


class Token:


    def __init__(self, kind, content="", rep="", r=None):
        """Initialize this token."""
        self.kind = kind

        self.content = content if content else str(self.kind)
        self.rep = rep
        self.r = r

    def __repr__(self):  # pragma: no cover
        return self.content

    def __str__(self):
        """Return the token content."""
        return self.rep if self.rep else self.content
