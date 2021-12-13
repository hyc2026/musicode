"""Parser logic that parses expression nodes."""
import musicode.mcparser.utils as p
import musicode.token_kinds as token_kinds
import musicode.tree.expr_nodes as expr_nodes
from musicode.mcparser.utils import (add_range, match_token, token_is, ParserError,
                                 raise_error, log_error, token_in)

"""
expression::= List(assignment_expression)
"""
@add_range
def parse_expression(index):
    """Parse expression."""
    return parse_series(
        index, parse_assignment,
        {token_kinds.comma: expr_nodes.MultiExpr})

"""
assignment_expression::= S(unary_expression, assignment_operator) # S(E,Op) = E Op E Op E Op ... E
assignment_operator::= "=" | "*=" | "/=" | "%=" | "+=" | "<<=" | ">>=" | "&=" | "^=" | "|="

"""
@add_range
def parse_assignment(index):
    """Parse an assignment expression."""

    # This is a slight departure from the official grammar. The standard
    # specifies that a program is syntactically correct only if the
    # left-hand side of an assignment expression is a unary expression. But,
    # to provide more helpful error messages, we permit the left side to be
    # any non-assignment expression.

    # left, index = parse_conditional(index) # E Op E Op E Op ... E，就这个语法，先parse个E，然后看下一个是不是OP，是的话接着parse E。conditional是优先级最低的
    left, index = parse_equality(index) # E Op E Op E Op ... E，就这个语法，先parse个E，然后看下一个是不是OP，是的话接着parse E。conditional是优先级最低的

    if index < len(p.tokens):
        op = p.tokens[index]
        kind = op.kind
    else:
        op = None
        kind = None

    node_types = {token_kinds.equals: expr_nodes.Equals,
                  token_kinds.plusequals: expr_nodes.PlusEquals,
                  token_kinds.minusequals: expr_nodes.MinusEquals,
                  token_kinds.starequals: expr_nodes.StarEquals,
                  token_kinds.divequals: expr_nodes.DivEquals,
                  token_kinds.modequals: expr_nodes.ModEquals}

    if kind in node_types:
        right, index = parse_assignment(index + 1)
        return node_types[kind](left, right, op), index
    else:
        return left, index

"""
conditional_expression::= logical_OR_expression
"""
@add_range
def parse_conditional(index):
    """Parse a conditional expression."""
    return parse_logical_or(index)

"""
logical_OR_expression::= S(logical_AND_expression, logical_OR_operator)
"""
@add_range
def parse_logical_or(index):
    """Parse logical or expression."""
    return parse_series(
        index, parse_logical_and,
        {token_kinds.bool_or: expr_nodes.BoolOr})

"""
logical_AND_expression::= S(OR_expression, logical_AND_operator) # 这里是bitwise OR
OR_expression::=S(XOR_expression, OR_operator)
"""
@add_range
def parse_logical_and(index):
    """Parse logical and expression."""
    # TODO: Implement bitwise operators here.
    return parse_series(
        index, parse_equality,
        {token_kinds.bool_and: expr_nodes.BoolAnd})

"""
equality_expression::= S(relational_expression, equality_operator)

"""
@add_range
def parse_equality(index):
    """Parse equality expression."""
    # TODO: Implement relational and shift expressions here.
    return parse_series(
        index, parse_relational,
        {token_kinds.twoequals: expr_nodes.Equality,
         token_kinds.notequal: expr_nodes.Inequality})

"""
relational_expression::= S(shift_expression, relational_operator)
"""
@add_range
def parse_relational(index):
    """Parse relational expression."""
    return parse_series(
        index, parse_bitwise,
        {token_kinds.lt: expr_nodes.LessThan,
         token_kinds.gt: expr_nodes.GreaterThan,
         token_kinds.ltoe: expr_nodes.LessThanOrEq,
         token_kinds.gtoe: expr_nodes.GreaterThanOrEq})

"""
shift_expression::= S(additive_expression, shift_operator)
"""
@add_range
def parse_bitwise(index):
    return parse_series(
        index, parse_additive,
        {token_kinds.lbitshift: expr_nodes.LBitShift,
         token_kinds.rbitshift: expr_nodes.RBitShift,
         token_kinds.bar: expr_nodes.BitOr,
         token_kinds.amp: expr_nodes.BitAnd
         })

"""
additive_expression::= S(multiplicative_expression, additive_operator)
This means that addition and subtraction occurs after multiplication and from left to right.
"""
@add_range
def parse_additive(index):
    """Parse additive expression."""
    return parse_series(
        index, parse_multiplicative,
        {token_kinds.plus: expr_nodes.Plus,
         token_kinds.minus: expr_nodes.Minus})

"""
multiplicative_expression::= S(cast_expression, multiplicative_operator)
The rule above means that 'casts' are done before multiplication and division, and that multiplication and division are done from left to right.
"""
@add_range
def parse_multiplicative(index):
    """Parse multiplicative expression."""
    return parse_series(
        index, parse_cast,
        {token_kinds.star: expr_nodes.Mult,
         token_kinds.slash: expr_nodes.Div,
         token_kinds.mod: expr_nodes.Mod,
         token_kinds.at: expr_nodes.At
         })

"""
cast_expression::= unary_expression. This implies that casts are done after doing post-fix operations
"""
@add_range
def parse_cast(index):
    """Parse cast expression."""

    return parse_unary(index)

"""
unary_expression::= #(pre-fix) post_fix_expression | unary_operator cast_expression
unary_operator::= "&" | "*" | "+" | "-" | "!" | "-"
pre_fix::= "++" | "--"
"""
@add_range
def parse_unary(index):
    """Parse unary expression."""

    unary_args = {token_kinds.incr: (parse_unary, expr_nodes.PreIncr),
                  token_kinds.decr: (parse_unary, expr_nodes.PreDecr),
                  # token_kinds.amp: (parse_cast, expr_nodes.AddrOf),
                  # token_kinds.star: (parse_cast, expr_nodes.Deref),
                  # token_kinds.bool_not: (parse_cast, expr_nodes.BoolNot),
                  token_kinds.plus: (parse_cast, expr_nodes.UnaryPlus),
                  token_kinds.minus: (parse_cast, expr_nodes.UnaryMinus),
                  token_kinds.compl: (parse_cast, expr_nodes.Compl)}

    if token_in(index, unary_args):
        parse_func, NodeClass = unary_args[p.tokens[index].kind]
        subnode, index = parse_func(index + 1)
        return NodeClass(subnode), index
    elif token_is(index, token_kinds.play_kw):
        with log_error():
            node, index = parse_unary(index + 1)
            return expr_nodes.PlayExpr(node), index

    else:
        return parse_postfix(index)


"""
post_fix_expression::= (primary_expression) #(post_fix)
post_fix::= "++" | "--" | "[" expression "]"
"""
@add_range
def parse_postfix(index):
    """Parse postfix expression."""
    cur, index = parse_primary(index)

    while True:
        old_range = cur.r
        if token_is(index, token_kinds.open_sq_brack):
            index += 1
            arg, index = parse_expression(index)
            cur = expr_nodes.ArraySubsc(cur, arg)
            index = match_token(index, token_kinds.close_sq_brack, ParserError.GOT)
        elif token_is(index, token_kinds.dot):
            index += 1
            suffix, index = parse_primary(index)
            cur = expr_nodes.Dot(cur, suffix, token_kinds.dot)
        elif token_is(index, token_kinds.incr):
            index += 1
            cur = expr_nodes.PostIncr(cur)
        elif token_is(index, token_kinds.decr):
            index += 1
            cur = expr_nodes.PostDecr(cur)
        else:
            return cur, index

        cur.r = old_range + p.tokens[index - 1].r

"""
primary_expression::= variable | constant | string_literal | "(" expression ")" | args
variable::= identifier & declared and in scope of declaration.
"""
@add_range
def parse_primary(index):
    """Parse primary expression."""
    if token_is(index, token_kinds.open_paren):
        node, index = parse_expression(index + 1)
        index = match_token(index, token_kinds.close_paren, ParserError.GOT)
        return expr_nodes.ParenExpr(node), index
    elif token_is(index, token_kinds.number):
        return expr_nodes.Number(p.tokens[index]), index + 1
    elif token_is(index, token_kinds.identifier):
        return expr_nodes.Identifier(p.tokens[index]), index + 1
    elif token_is(index, token_kinds.string):
        return expr_nodes.String(p.tokens[index].content), index + 1
    elif token_is(index, token_kinds.char_string):
        chars = p.tokens[index].content
        return expr_nodes.Number(chars[0]), index + 1
    elif token_is(index, token_kinds.open_brack):
        return parse_args(index)

    else:
        raise_error("expected expression", index, ParserError.GOT)


def parse_series(index, parse_base, separators):
    """Parse a series of symbols joined together with given separator(s).

    index (int) - Index at which to start searching.
    parse_base (function) - A parse_* function that parses the base symbol.
    separators (Dict(TokenKind -> Node)) - The separators that join
    instances of the base symbol. Each separator corresponds to a Node,
    which is the Node produced to join two expressions connected with that
    separator.
    """
    cur, index = parse_base(index)
    while True:
        for s in separators:
            if token_is(index, s):
                break
        else:
            return cur, index

        tok = p.tokens[index]
        new, index = parse_base(index + 1)
        cur = separators[s](cur, new, tok)

"""
args::= "{"expression"}"
"""
@add_range
def parse_args(index):
    args = []
    index = match_token(
        index, token_kinds.open_brack, ParserError.GOT)
    if token_is(index, token_kinds.close_brack):
        return expr_nodes.Args(args), index + 1

    while True:
        arg, index = parse_assignment(index)
        args.append(arg)

        if token_is(index, token_kinds.comma):
            index += 1
        else:
            break

    index = match_token(
        index, token_kinds.close_brack, ParserError.GOT)

    return expr_nodes.Args(args), index
