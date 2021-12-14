
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

    node, index = parse_decls_inits(index)
    return nodes.Declaration(node), index # nodes.Declatation是为make_il准备的，继承自Node， parse_decls_inits返回的node主要存的是声明的内容（标识符，类型等）

"""
declarator::= identifier | direct_declarator post_declarator
post_declarator::= "["constant_expression"]"
"""
@add_range
def parse_declarator(index):

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






