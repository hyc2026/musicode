
import musicode.mcparser.utils as p
import musicode.tree.nodes as nodes

from musicode.errors import error_collector
from musicode.mcparser.utils import (add_range, log_error, ParserError,
                                 raise_error)
from musicode.mcparser.declaration import parse_declaration
from musicode.mcparser.statement import parse_statement


def parse(tokens_to_parse):

    p.best_error = None
    p.tokens = tokens_to_parse

    with log_error():
        return parse_root(0)[0]

    error_collector.add(p.best_error)
    return None


@add_range
def parse_root(index):
    """Parse the given tokens into an AST."""
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

        # If neither parse attempt above worked, break
        break

    # If there are tokens that remain unparsed, complain
    if not p.tokens[index:]:
        return nodes.Root(items), index
    else:
        raise_error("unexpected token", index, ParserError.AT)
