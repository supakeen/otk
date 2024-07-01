import argparse
import logging
import pathlib
import sys
from typing import List

from .document import Omnifest
from .target import OSBuildTarget

log = logging.getLogger(__name__)


def root() -> int:
    return run(sys.argv[1:])


def run(argv: List[str]) -> int:
    parser = parser_create()
    arguments = parser.parse_args(argv)

    # turn on logging as *soon* as possible, so it can be used early
    logging.basicConfig(
        level=logging.WARNING - (10 * arguments.verbose),
        handlers=[logging.StreamHandler()],
    )

    if arguments.command == "compile":
        return compile(arguments)
    if arguments.command == "validate":
        return validate(arguments)

    raise RuntimeError("Unknown subcommand")


def _process(arguments: argparse.Namespace, dry_run: bool) -> int:
    if not dry_run:
        # pylint: disable=R1732
        dst = sys.stdout if arguments.output is None else open(arguments.output, "w", encoding="utf-8")

    if arguments.input is None:
        path = pathlib.Path(f"/proc/self/fd/{sys.stdin.fileno()}")
    else:
        path = pathlib.Path(arguments.input)

    warn_duplicated_defs = any(arg in getattr(arguments, "warn", [])
                               for arg in ["duplicate-definition", "all"])
    # First pass of resolving the otk file is "shallow", it will not run
    # externals and not resolve anything under otk.target.*
    #
    # It only exists as convenience for the user so that they do not need
    # to use "-t"
    doc = Omnifest(path, warn_duplicated_defs=warn_duplicated_defs)

    target_available = doc.targets
    target_requested = arguments.target
    if not target_requested:
        if len(target_available) > 1:
            log.fatal("INPUT contains multiple targets, `-t` is required")
            return 1
        # set the requested target to the default case now that we know that
        # there aren't multiple targets available and none are requested
        target_requested = list(target_available.keys())[0]

    if target_requested not in target_available:
        log.fatal("requested target %r does not exist in INPUT", target_requested)
        return 1

    # Now do the real resolve that takes the target into account. It needs
    # a full run so that resolving includes works correctly.
    doc = Omnifest(path, target=target_requested, warn_duplicated_defs=warn_duplicated_defs)
    target = OSBuildTarget()
    if not target.is_valid(doc._tree):
        return 1

    # and then output by writing to the output
    if not dry_run:
        dst.write(doc.as_target_string())

    return 0


def compile(arguments: argparse.Namespace) -> int:  # pylint: disable=redefined-builtin
    return _process(arguments, dry_run=False)


def validate(arguments: argparse.Namespace) -> int:
    return _process(arguments, dry_run=True)


def parser_create() -> argparse.ArgumentParser:
    # set up the main parser arguments
    parser = argparse.ArgumentParser(
        prog="otk",
        description="`otk` is the omnifest toolkit. A program to work with "
        "omnifest inputs and translate them into the native formats for image "
        "build tooling.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Sets verbosity. Can be passed multiple times to be more verbose.",
    )
    parser.add_argument(
        "-W",
        "--warn",
        action='append',
        default=[],
        help="Enable warnings, use 'all' to get all or enable specific warnings. Can be passed multiple times.",
    )

    # get a subparser action
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="command")

    parser_compile = subparsers.add_parser("compile", help="Compile an omnifest.")
    parser_compile.add_argument(
        "input",
        metavar="INPUT",
        nargs="?",
        default=None,
        help="Omnifest to compile to or none for STDIN.",
    )
    parser_compile.add_argument(
        "-o",
        "--output",
        default=None,
        help="File to output to or none for STDOUT.",
    )
    parser_compile.add_argument(
        "-t",
        "--target",
        default=None,
        help="Target to output, required if more than one target exists in an omnifest.",
    )

    parser_validate = subparsers.add_parser("validate", help="Validate an omnifest.")
    parser_validate.add_argument(
        "input",
        metavar="INPUT",
        nargs="?",
        default=None,
        help="Omnifest to validate to or none for STDIN.",
    )
    parser_validate.add_argument(
        "-t",
        "--target",
        default=None,
        help="Target to validate, required if more than one target exists in an omnifest.",
    )

    return parser
