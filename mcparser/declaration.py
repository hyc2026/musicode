"""Parser logic that parses declaration nodes.

The functions in this file that have names beginning with an underscore are
to be considered implementation details of the declaration parsing. That is,
they are helpers for the other functions rather than meant to be used
directly. The primary purpose for this distinction is to enhance parser
readablity.

"""

import musicode.musictypes as musictypes
from musicode.errors import error_collector, CompilerError
import musicode.mcparser.utils as p
import musicode.token_kinds as token_kinds
import musicode.tree.decl_nodes as decl_nodes
import musicode.tree.nodes as nodes
from musicode.mcparser.expression import parse_expression
from musicode.mcparser.utils import (add_range, ParserError, match_token, token_is,
                                 raise_error, log_error, token_in)




@add_range
def parse_declaration(index):
    """Parse a declaration into a tree.nodes.Declaration node.

    Example:
        note a, b

    """
    node, index = parse_decls_inits(index)
    return nodes.Declaration(node), index # nodes.Declatation是为make_il准备的，继承自Node， parse_decls_inits返回的node主要存的是声明的内容（标识符，类型等）

"""
declarator::= identifier | direct_declarator post_declarator
post_declarator::= "["constant_expression"]"
"""
@add_range
def parse_declarator(index):
    """Parse the tokens that comprise a declarator.

    A declarator is the part of a declaration that comes after the
    declaration specifiers (note, chord, etc.) but before any initializers.
    For example, in `note a` the declarator is `a`.


    Returns a decl_nodes.Node and index.
    """
    end = _find_decl_end(index)
    return _parse_declarator(index, end), end




"""
declaration::= declaration_specifier | declarator_list
declaration_specifier::= "note" | "chord"
declarator_list::= List(declarator_initialized)
declarator_initialized::= declarator ("=" initializer)
initializer::= assignment_expression | initializer_list
initializer_list::= List(initializer)

declarator::= identifier | direct_declarator post_declarator
post_declarator::= "["constant_expression"]"
"""
@add_range
def parse_decls_inits(index, parse_inits=True):

    """Parse declarations and initializers into a decl_nodes.Root node.

    Ex:
       note a = 'C5', b = 'B4';

    The decl_nodes node can be used by the caller to create a
    tree.nodes.Declaration node, and the decl_nodes node is traversed during
    the IL generation step to convert it into an appropriate musictype.

    If `parse_inits` is false, do not permit initializers.

    Note that parse_declaration is simply a wrapper around this function. The
    reason this logic is not in parse_declaration directly is so that struct
    member list parsing can reuse this logic.
    """
    specs, index = parse_decl_specifiers(index)

    # If declaration specifiers are followed directly by semicolon
    if token_is(index, token_kinds.semicolon):
        return decl_nodes.Root(specs, []), index + 1

    decls = []
    inits = []

    while True:
        node, index = parse_declarator(index)
        decls.append(node)

        if token_is(index, token_kinds.equals) and parse_inits:
            # Parse initializer expression
            from musicode.mcparser.expression import parse_assignment
            expr, index = parse_assignment(index + 1)
            inits.append(expr)
        else:
            inits.append(None)

        # Expect a comma, break if there isn't one
        if token_is(index, token_kinds.comma):
            index += 1
        else:
            break

    index = match_token(index, token_kinds.semicolon, ParserError.AFTER)

    node = decl_nodes.Root(specs, decls, inits)
    return node, index

"""
declaration_specifier::= "note" | "chord"
"""
def parse_decl_specifiers(index, _spec_qual=False):
    """Parse a declaration specifier list.

    Examples:
        note
        chord
    """
    type_specs = set(musictypes.simple_types.keys())

    specs = []

    if token_in(index, type_specs):
        specs.append(p.tokens[index])
        index += 1

    if specs:
        return specs, index
    else:
        raise_error("expected declaration specifier", index, ParserError.AT)



def _find_pair_forward(index,
                       open=token_kinds.open_paren,
                       close=token_kinds.close_paren,
                       mess="mismatched parentheses in declaration"):
    """Find the closing parenthesis for the opening at given index.

    index - position to start search, should be of kind `open`
    open - token kind representing the open parenthesis
    close - token kind representing the close parenthesis
    mess - message for error on mismatch
    """
    depth = 0
    for i in range(index, len(p.tokens)):
        if p.tokens[i].kind == open:
            depth += 1
        elif p.tokens[i].kind == close:
            depth -= 1

        if depth == 0:
            break
    else:
        # if loop did not break, no close paren was found
        raise_error(mess, index, ParserError.AT)
    return i


def _find_pair_backward(index,
                        open=token_kinds.open_paren,
                        close=token_kinds.close_paren,
                        mess="mismatched parentheses in declaration"):
    """Find the opening parenthesis for the closing at given index.

    Same parameters as _find_pair_forward above.
    """
    depth = 0
    for i in range(index, -1, -1):
        if p.tokens[i].kind == close:
            depth += 1
        elif p.tokens[i].kind == open:
            depth -= 1

        if depth == 0:
            break
    else:
        # if loop did not break, no open paren was found
        raise_error(mess, index, ParserError.AT)
    return i


def _find_decl_end(index):
    """Find the end of the declarator that starts at given index.

    If a valid declarator starts at the given index, this function is
    guaranteed to return the correct end point. Returns an index one
    greater than the last index in this declarator.
    """
    if token_is(index, token_kinds.identifier) :
        return _find_decl_end(index + 1)
    elif token_is(index, token_kinds.open_sq_brack):
        mess = "mismatched square brackets in declaration"
        close = _find_pair_forward(index, token_kinds.open_sq_brack,
                                   token_kinds.close_sq_brack, mess)
        return _find_decl_end(close + 1)
    else:
        # Unknown token. If this declaration is correctly formatted,
        # then this must be the end of the declaration.
        return index


def _parse_declarator(start, end):
    """Parses a declarator between start and end.

    Expects the declarator to start at start and end at end-1 inclusive.
    Prefer to use the parse_declarator function externally over this function.
    """
    decl = _parse_declarator_raw(start, end)
    decl.r = p.tokens[start].r + p.tokens[end - 1].r
    return decl


def _parse_declarator_raw(start, end):
    """Like _parse_declarator, but doesn't add `.r` range attribute."""

    if start == end:
        return decl_nodes.Identifier(None)

    elif (start + 1 == end and
           p.tokens[start].kind == token_kinds.identifier):
        p.symbols.add_symbol(p.tokens[start])
        return decl_nodes.Identifier(p.tokens[start])

    # Last element indicates an array type
    elif p.tokens[end - 1].kind == token_kinds.close_sq_brack:
        open_sq = _find_pair_backward(
            end - 1, token_kinds.open_sq_brack, token_kinds.close_sq_brack,
            "mismatched square brackets in declaration")

        if open_sq == end - 2:
            num_el = None
        else:
            num_el, index = parse_expression(open_sq + 1)
            if index != end - 1:
                err = "unexpected token in array size"
                raise_error(err, index, ParserError.AFTER)

        return decl_nodes.Array(
            num_el, _parse_declarator(start, open_sq))

    raise_error("faulty declaration syntax", start, ParserError.AT)






