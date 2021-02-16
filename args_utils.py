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


DEFAULT_MAX_FILES = 100
DEFAULT_MAX_FUTURES = 50


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

    if args.out_file is not None and args.out_file.suffix != "":

        if args.out_file.suffix != ".csv":

            print(
                f"""
As a general heads up your out-file will always be a .csv
Even though you provided an out-file with the extension {args.out_file.suffix},
it will be changed to {args.out_file.with_suffix('.csv').__str__()}                  
"""
            )

        vars(args)["out_file"] = args.out_file.with_suffix("")

    if args.out_file is not None and args.out_file.with_suffix(".csv").exists():

        print(f'{args.out_file.with_suffix(".csv")} already exists.')

        idx = 2

        new_file_name = args.out_file.name

        while args.out_file.with_name(new_file_name).with_suffix(".csv").exists():

            new_file_name = args.out_file.stem + f" ({idx})"

            idx += 1

        print(
            f'Instead the out_file will be {args.out_file.with_name(new_file_name).with_suffix(".csv").__str__()}\n\n'
        )

        vars(args)["out_file"] = args.out_file.with_name(new_file_name)

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
        help="The location to search. Default is the current directory.",
    )

    arg_parser.add_argument(
        "-i",
        "--case-insensitive",
        action="store_true",
        help="If provided, will turn off case-sensitivity.",
    )

    arg_parser.add_argument(
        "-ln",
        "--line-num",
        action="store_true",
        help="If provided, will add a column to the results identifying what lines a search term showed up in within the file.",
    )

    arg_parser.add_argument(
        "-dta", "--dirs-to-avoid", nargs="*", help="Directories to avoid searching."
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
        default=DEFAULT_MAX_FUTURES,
        help=f"The number of futures allowed in a group before pausing to resolve them. Default is {DEFAULT_MAX_FUTURES}.",
    )

    arg_parser.add_argument(
        "-mfi",
        "--max-files",
        nargs="?",
        type=int,
        default=DEFAULT_MAX_FILES,
        help=f"The max number of files to process in each batch. Default is {DEFAULT_MAX_FILES}.",
    )

    arg_parser.add_argument(
        "-p",
        "--processes",
        nargs="?",
        type=int,
        default=cpu_count(),
        help=f"The number of processes to use. Default is {cpu_count()}.",
    )

    arg_parser.add_argument(
        "-o",
        "--output",
        choices=OUTPUT_CHOICES,
        default=OUTPUT_PRINT,
        help="How to provide the results. Default is stdout.",
    )

    arg_parser.add_argument(
        "-of",
        "--out-file",
        type=Path,
        help="A filepath or filename to save the result to. Default is a generated name.",
    )

    arg_parser.add_argument(
        "-st",
        "--search-terms",
        nargs=REMAINDER,
        help="The terms to search for. Must be the last argument.",
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
