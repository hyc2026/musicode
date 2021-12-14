
import re

import musicode.token_kinds as token_kinds
from musicode.errors import CompilerError, Position, Range, error_collector
from musicode.tokens import Token
from musicode.token_kinds import symbol_kinds, keyword_kinds

class Tagged:


    def __init__(self, c, p):
        """Initialize object."""
        self.c = c
        self.p = p
        self.r = Range(p, p)


def tokenize(code, filename):

    # Store tokens as they are generated
    tokens = []

    lines = split_to_tagged_lines(code, filename)
    join_extended_lines(lines) # 支持行末/换行接着写

    in_comment = False
    for line in lines:
        try:
            line_tokens, in_comment = tokenize_line(line, in_comment)
            tokens += line_tokens
        except CompilerError as e:
            error_collector.add(e)

    return tokens


def split_to_tagged_lines(text, filename):

    lines = text.splitlines()
    tagged_lines = []
    for line_num, line in enumerate(lines):
        tagged_line = []
        for col, char in enumerate(line):
            p = Position(filename, line_num + 1, col + 1, line)
            tagged_line.append(Tagged(char, p))
        tagged_lines.append(tagged_line)

    return tagged_lines


def join_extended_lines(lines):

    i = 0
    while i < len(lines):
        if lines[i] and lines[i][-1].c == "\\":
            # There is a next line to collapse into this one
            if i + 1 < len(lines):
                del lines[i][-1]  # remove trailing backslash
                lines[i] += lines[i + 1]  # concatenate with next line
                del lines[i + 1]  # remove next line

                # Decrement i, so this line is checked for a new trailing
                # backslash.
                i -= 1

            # There is no next line to collapse into this one
            else:
                # TODO: print warning?
                del lines[i][-1]  # remove trailing backslash

        i += 1


def tokenize_line(line, in_comment):

    tokens = []


    chunk_start = 0
    chunk_end = 0


    while chunk_end < len(line):
        symbol_kind = match_symbol_kind_at(line, chunk_end)
        next_symbol_kind = match_symbol_kind_at(line, chunk_end + 1)

        if in_comment:
            # If next characters end the comment...
            if (symbol_kind == token_kinds.star and
                    next_symbol_kind == token_kinds.slash):
                in_comment = False
                chunk_start = chunk_end + 2
                chunk_end = chunk_start
            # Otherwise, just skip one character.
            else:
                chunk_start = chunk_end + 1
                chunk_end = chunk_start

        # If next characters start a comment, process previous chunk and set
        # in_comment to true.
        elif (symbol_kind == token_kinds.slash and
                next_symbol_kind == token_kinds.star):
            add_chunk(line[chunk_start:chunk_end], tokens)
            in_comment = True

        # If next two characters are //, we skip the rest of this line.
        elif (symbol_kind == token_kinds.slash and
                next_symbol_kind == token_kinds.slash):
            break

        # Skip spaces and process previous chunk.
        elif line[chunk_end].c.isspace():
            add_chunk(line[chunk_start:chunk_end], tokens)
            chunk_start = chunk_end + 1
            chunk_end = chunk_start

        # If next character is a quote, we read the whole string as a token.
        elif symbol_kind in {token_kinds.dquote, token_kinds.squote}:
            if symbol_kind == token_kinds.dquote:
                quote_str = '"'
                kind = token_kinds.string
                add_null = True
            else:
                quote_str = "'"
                kind = token_kinds.char_string
                add_null = False

            chars, end = read_string(line, chunk_end + 1, quote_str, add_null)
            rep = chunk_to_str(line[chunk_end:end + 1])
            r = Range(line[chunk_end].p, line[end].p)

            if kind == token_kinds.char_string and len(chars) == 0:
                err = "empty character constant"
                error_collector.add(CompilerError(err, r))
            elif kind == token_kinds.char_string and len(chars) > 1:
                err = "multiple characters in character constant"
                error_collector.add(CompilerError(err, r))

            tokens.append(Token(kind, chars, rep, r=r))

            chunk_start = end + 1
            chunk_end = chunk_start

        # If next character is another symbol, add previous chunk and then
        # add the symbol.
        elif symbol_kind:
            symbol_start_index = chunk_end
            symbol_end_index = chunk_end + len(symbol_kind.text_repr) - 1

            r = Range(line[symbol_start_index].p, line[symbol_end_index].p)
            symbol_token = Token(symbol_kind, r=r)

            add_chunk(line[chunk_start:chunk_end], tokens)
            tokens.append(symbol_token)

            chunk_start = chunk_end + len(symbol_kind.text_repr)
            chunk_end = chunk_start

        # Include another character in the chunk.
        else:
            chunk_end += 1

    # Flush out anything that is left in the chunk to the output
    add_chunk(line[chunk_start:chunk_end], tokens)



    return tokens, in_comment


def chunk_to_str(chunk):

    return "".join(c.c for c in chunk)


def match_symbol_kind_at(content, start):

    for symbol_kind in symbol_kinds:
        try:
            for i, c in enumerate(symbol_kind.text_repr):
                if content[start + i].c != c:
                    break
            else:
                return symbol_kind
        except IndexError:
            pass

    return None



def read_string(line, start, delim, null):

    i = start
    chars = []

    escapes = {"'": 39,
               '"': 34,
               "?": 63,
               "\\": 92,
               "a": 7,
               "b": 8,
               "f": 12,
               "n": 10,
               "r": 13,
               "t": 9,
               "v": 11}
    octdigits = "01234567"
    hexdigits = "0123456789abcdefABCDEF"

    while True:
        if i >= len(line):
            descrip = "missing terminating quote"
            raise CompilerError(descrip, line[start - 1].r)
        elif line[i].c == delim:
            if null: chars.append(0)
            return chars, i
        elif (i + 1 < len(line)
              and line[i].c == "\\"
              and line[i + 1].c in escapes):
            chars.append(escapes[line[i + 1].c])
            i += 2
        elif (i + 1 < len(line)
              and line[i].c == "\\"
              and line[i + 1].c in octdigits):
            octal = line[i + 1].c
            i += 2
            while (i < len(line)
                   and len(octal) < 3
                   and line[i].c in octdigits):
                octal += line[i].c
                i += 1
            chars.append(int(octal, 8))
        elif (i + 2 < len(line)
              and line[i].c == "\\"
              and line[i + 1].c == "x"
              and line[i + 2].c in hexdigits):
            hexa = line[i + 2].c
            i += 3
            while i < len(line) and line[i].c in hexdigits:
                hexa += line[i].c
                i += 1
            chars.append(int(hexa, 16))
        else:
            chars.append(ord(line[i].c))
            i += 1



def add_chunk(chunk, tokens):

    if chunk:
        range = Range(chunk[0].p, chunk[-1].p)

        keyword_kind = match_keyword_kind(chunk)
        if keyword_kind:
            tokens.append(Token(keyword_kind, r=range))
            return

        number_string = match_number_string(chunk)
        if number_string:
            tokens.append(Token(token_kinds.number, number_string, r=range))
            return

        identifier_name = match_identifier_name(chunk)
        if identifier_name:
            tokens.append(Token(
                token_kinds.identifier, identifier_name, r=range))
            return

        descrip = f"unrecognized token at '{chunk_to_str(chunk)}'"
        raise CompilerError(descrip, range)


def match_keyword_kind(token_repr):
    """Find the longest keyword token kind with representation token_repr.

    token_repr - Token representation to match exactly, as list of Tagged
    characters.
    returns (TokenKind, or None) - Keyword token kind that matched.

    """
    token_str = chunk_to_str(token_repr)
    for keyword_kind in keyword_kinds:
        if keyword_kind.text_repr == token_str:
            return keyword_kind
    return None


def match_number_string(token_repr):
    """Return a string that represents the given constant number.

    token_repr - List of Tagged characters.
    returns (str, or None) - String representation of the number.

    """
    token_str = chunk_to_str(token_repr)
    # return token_str if token_str.isdigit() else None
    return token_str if token_str.isdigit() else None


def match_identifier_name(token_repr):

    token_str = chunk_to_str(token_repr)
    if re.match(r"[_a-zA-Z][_a-zA-Z0-9]*$", token_str):
        return token_str
    else:
        return None


def IsFloatNum(str):
    s=str.split('.')
    if len(s)>2:
        return False
    else:
        for si in s:
            if not si.isdigit():
                return False
        return True
