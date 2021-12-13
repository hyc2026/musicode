"""Parser logic that parses statement nodes."""
import musicode.token_kinds as token_kinds
import musicode.tree.nodes as nodes
import musicode.mcparser.utils as p

from musicode.mcparser.declaration import parse_declaration
from musicode.mcparser.expression import parse_expression
from musicode.mcparser.utils import (add_range, log_error, match_token, token_is,
                                 ParserError)


"""
statement::= labeled_statement | compound_statement | expression_statement | selection_statement | iteration_statement | jump_statement
"""
@add_range
def parse_statement(index):
    """Parse a statement.

    Try each possible type of statement, catching/logging exceptions upon
    parse failures. On the last try, raise the exception on to the caller.

    """
    for func in (
            parse_break,
            parse_continue,
            parse_if_statement,
            parse_while_statement
    ):
        with log_error():
            return func(index)

    return parse_expr_statement(index)

"""
compound_statement::= block | "{" #statement "}"
block::= "{" declaration #declaration #statement "}"
"""
@add_range
def parse_compound_statement(index):
    """Parse a compound statement.

    A compound statement is a collection of several
    statements/declarations, enclosed in braces.

    """
    p.symbols.new_scope()
    index = match_token(index, token_kinds.open_brack, ParserError.GOT)

    # Read block items (statements/declarations) until there are no more.
    items = []
    while True:
        with log_error():
            item, index = parse_statement(index)
            items.append(item)
            continue

        with log_error():
            item, index = parse_declaration(index)
            items.append(item)
            continue

        break

    index = match_token(index, token_kinds.close_brack, ParserError.GOT)
    p.symbols.end_scope()

    return nodes.Compound(items), index


@add_range
def parse_break(index):
    """Parse a break statement."""
    index = match_token(index, token_kinds.break_kw, ParserError.GOT)
    index = match_token(index, token_kinds.semicolon, ParserError.AFTER)
    return nodes.Break(), index


@add_range
def parse_continue(index):
    """Parse a continue statement."""
    index = match_token(index, token_kinds.continue_kw, ParserError.GOT)
    index = match_token(index, token_kinds.semicolon, ParserError.AFTER)
    return nodes.Continue(), index

"""
if_statement::= "if ("expression")" statement | "if" "("expression")" statement "else" statement
"""
@add_range
def parse_if_statement(index):
    """Parse an if statement."""

    index = match_token(index, token_kinds.if_kw, ParserError.GOT)
    index = match_token(index, token_kinds.open_paren, ParserError.AFTER)
    conditional, index = parse_expression(index)
    index = match_token(index, token_kinds.close_paren, ParserError.AFTER)
    statement, index = parse_statement(index)

    # If there is an else that follows, parse that too.
    is_else = token_is(index, token_kinds.else_kw)
    if not is_else:
        else_statement = None
    else:
        index = match_token(index, token_kinds.else_kw, ParserError.GOT)
        else_statement, index = parse_statement(index)

    return nodes.IfStatement(conditional, statement, else_statement), index

"""
iteration_statement::= "while" "("expression")" statement
"""
@add_range
def parse_while_statement(index):
    """Parse a while statement."""
    index = match_token(index, token_kinds.while_kw, ParserError.GOT)
    index = match_token(index, token_kinds.open_paren, ParserError.AFTER)
    conditional, index = parse_expression(index)
    index = match_token(index, token_kinds.close_paren, ParserError.AFTER)
    statement, index = parse_statement(index)

    return nodes.WhileStatement(conditional, statement), index


"""
expression_statement::= expression ";"
"""
@add_range
def parse_expr_statement(index):
    """Parse a statement that is an expression.

    Ex: a = b + 1

    """
    if token_is(index, token_kinds.semicolon):
        return nodes.EmptyStatement(), index + 1

    node, index = parse_expression(index)
    index = match_token(index, token_kinds.semicolon, ParserError.AFTER)
    return nodes.ExprStatement(node), index
