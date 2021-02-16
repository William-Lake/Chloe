from argparse import ArgumentParser, RawTextHelpFormatter, REMAINDER
from multiprocessing import cpu_count
from pathlib import Path
from sys import exit

from colorama import Fore, Back, Style

from output_utils import (
    OUTPUT_CHOICES,
    OUTPUT_FILE,
    OUTPUT_PRINT,
)


def args_acceptable(args):

    search_loc = args.search_loc

    search_terms = args.search_terms

    if not search_loc.exists():

        return False, f"{search_loc.__str__()} could not be found!"

    if search_terms is None:

        search_terms = []

    search_terms = [
        term for term in search_terms if term is not None and len(term.strip()) > 0
    ]

    if not search_terms:

        return False, "Please provide at least one search term!"

    if args.max_futures <= 0:

        return False, "The number of futures in the batch must be >= 1!"

    if args.max_files <= 1:

        return False, "The number of files in the batch must be > 1!"

    if args.processes <= 0:

        return False, "The number of proceses must be >= 1!"

    if args.processes > cpu_count():

        return False, f"The number of processes must be <= {cpu_count()}!"

    return True, None


def gather_args(debug=False):

    arg_parser = ArgumentParser(
        formatter_class=RawTextHelpFormatter,
        prog="CHLOE.exe",
        description="Recursively searches a directory of files for a given value.",
    )

    arg_parser.add_argument(
        "search_loc",
        type=Path,
        nargs="?",
        default=Path("."),
        help="The location to search",
    )

    arg_parser.add_argument(
        "-dta", "--dirs-to-avoid", nargs="*", help="Directories to avoid searching."
    )

    arg_parser.add_argument(
        "-o",
        "--output",
        choices=OUTPUT_CHOICES,
        default=OUTPUT_PRINT,
        help="How to provide the results.",
    )

    arg_parser.add_argument(
        "-te",
        "--target-exts",
        nargs="*",
        help="Used if you only want to search within files with particular extensions.",
    )

    arg_parser.add_argument(
        "-eta",
        "--exts-to-avoid",
        nargs="*",
        help="Used if you want to avoid searching within files with particular extensions.",
    )

    arg_parser.add_argument(
        "-mfu",
        "--max-futures",
        nargs="?",
        type=int,
        default=50,
        help="The number of futures allowed in a group before pausing to resolve them.",
    )

    arg_parser.add_argument(
        "-mfi",
        "--max-files",
        nargs="?",
        type=int,
        default=100,
        help="The max number of files allowed in each processing batch.",
    )

    arg_parser.add_argument(
        "-p",
        "--processes",
        nargs="?",
        type=int,
        default=cpu_count(),
        help="The number of processes to use.",
    )

    arg_parser.add_argument(
        "-ln",
        "--line-num",
        action="store_true",
        help="If provided, will add a column to the results identifying what lines a search term showed up in within the file.",
    )

    arg_parser.add_argument(
        "-i",
        "--case-insensitive",
        action="store_true",
        help="If provided, will turn off case-sensitivity.",
    )

    arg_parser.add_argument(
        "-st", "--search-terms", nargs=REMAINDER, help="The terms to search for."
    )

    if debug:

        return arg_parser.parse_args(
            [
                r"C:\Users\cma726\MI-eclipse-workspace\DOA_ePass\epass-store",
                "--search_terms",
                "password",
                "--dirs_to_avoid",
                '".git"',
                "target",
                "--output",
                OUTPUT_FILE,
            ]
        )

    else:

        args = arg_parser.parse_args()

        args_ok, error_message = args_acceptable(args)

        if args_ok:

            return args

        else:

            arg_parser.print_help()

            print(error_message)

            exit()
