
import argparse

import sys

from ete3 import Tree

import musicode.lexer as lexer

from musicode.errors import error_collector, CompilerError
from musicode.mcparser.parser import parse
from musicode.il_gen import ILCode, SymbolTable, Context
from musicode.tree.nodes import Root as nRoot
from musicode.tree.nodes import Declaration, ExprStatement, Compound
from musicode.tree.decl_nodes import Root, Identifier
from musicode.tree.expr_nodes import Args, _RExprNode, Number, PlayExpr, String, ParenExpr
from musicode.tree.expr_nodes import Identifier as eIdentifier

def main():
    """Run the main compiler script."""

    arguments = get_arguments()

    # arguments.files = ['test.mc']

    objs = []
    for file in arguments.files:
        objs.append(process_file(file))

    error_collector.show()
    if any(not obj for obj in objs):
        return 1
    else:
        return 0


def process_file(file):

    if file[-3:] == ".mc":
        return process_mc_file(file)
    else:
        err = f"unknown file type: '{file}'"
        error_collector.add(CompilerError(err))
        return None


def ordered(node):
    strs = ""
    if isinstance(node, nRoot):
        strs += "("
        for i in node.nodes:
            strs += ordered(i)
        if strs.endswith(','):
            strs = strs[:-1]
        strs += ")"
    elif isinstance(node, Compound):
        strs += "Compound " + str(type(node.items))
        strs += ','
    elif isinstance(node, Declaration):
        strs += ordered(node.node)
        strs += ','
    elif isinstance(node, ExprStatement):
        strs += ordered(node.expr)
        strs += ','
    elif isinstance(node, Root):
        if node.inits[0] == None:
            strs += str(node.specs[0]) + " " + str(node.decls[0].identifier)
        else:    
            strs += "(" + str(node.specs[0]) + " " + str(node.decls[0].identifier) + " =," + ordered(node.inits[0]) + ")"
    elif isinstance(node, Args):
        strs += "("
        for i in node.args:
            strs += ordered(i)
            strs += ","
        if strs.endswith(','):
            strs = strs[:-1]
        strs += ")"
    elif isinstance(node, Number):
        strs += str(node.number)
    elif isinstance(node, Identifier) or isinstance(node, eIdentifier):
        strs += str(node.identifier)
    elif isinstance(node, PlayExpr):
        strs += "play" + ordered(node.expr)
    elif isinstance(node, String):
        for i in node.chars:
            if i:
                strs += chr(i)
    elif isinstance(node, _RExprNode):
        strs += "("
        strs += ordered(node.left)
        strs += "," + str(node.op) + ","
        strs += ordered(node.right)
        strs += ")"
    elif isinstance(node, ParenExpr):
        strs += " - " + ordered(node.expr)
    else:
        strs += str(type(node))
    # if strs.endswith(','):
    #     strs = strs[:-1]
    return strs


def process_mc_file(file):

    code = read_file(file)
    if not error_collector.ok():
        return None

    token_list = lexer.tokenize(code, file)
    if not error_collector.ok():
        return None

    ast_root = parse(token_list)
    if not ast_root:
        return None

    il_code = ILCode()
    symbol_table = SymbolTable()
    ast_root.make_il(il_code, symbol_table, Context())
    strs = ordered(ast_root)
    strs += ";"
    # print(strs)
    t = Tree(strs, format=1)
    print(t)
    if not error_collector.ok():
        return None

    return 1


def get_arguments():
    """Get the command-line arguments.

    This function sets up the argument parser. Returns a tuple containing
    an object storing the argument values and a list of the file names
    provided on command line.
    """
    desc = "Compile musicode files with .mc suffix"
    parser = argparse.ArgumentParser(
        description=desc, usage="musicode [-h] [options] files...")

    # Files to compile
    parser.add_argument("files", metavar="files", nargs="+")


    return parser.parse_args()


def read_file(file):
    """Return the contents of the given file."""
    try:
        with open(file) as mc_file:
            return mc_file.read()
    except IOError as e:
        descrip = f"could not read file: '{file}'"
        error_collector.add(CompilerError(descrip))



if __name__ == "__main__":
    sys.exit(main())
