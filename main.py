
import argparse

import sys

import musicode.lexer as lexer

from musicode.errors import error_collector, CompilerError
from musicode.mcparser.parser import parse
from musicode.il_gen import ILCode, SymbolTable, Context


def main():
    """Run the main compiler script."""

    arguments = get_arguments()

    arguments.files = ['assets/operator.mc']

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


def process_mc_file(file):

    code = read_file(file)
    if not error_collector.ok():
        return None

    token_list = lexer.tokenize(code, file)
    if not error_collector.ok():
        return None

    # If parse() can salvage the input into a parse tree, it may emit an
    # ast_root even when there are errors saved to the error_collector. In this
    # case, we still want to continue the compiler stages.
    ast_root = parse(token_list)
    if not ast_root:
        return None

    il_code = ILCode()
    symbol_table = SymbolTable()
    ast_root.make_il(il_code, symbol_table, Context())
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
