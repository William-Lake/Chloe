from argparse import ArgumentParser, RawTextHelpFormatter
from multiprocessing import cpu_count
from pathlib import Path
from sys import exit

from colorama import Fore, Back, Style

from output_utils import OUTPUT_CHOICES, OUTPUT_FILE, OUTPUT_PRINT


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

    if args.num_futures_in_batch <= 0:

        return False, "The number of futures in the batch must be >= 1!"

    if args.num_files_in_batch <= 1:

        return False, "The number of files in the batch must be > 1!"

    if args.num_processes <= 0:

        return False, "The number of proceses must be >= 1!"

    if args.num_processes > cpu_count():

        return False, f"The number of processes must be <= {cpu_count()}!"

    return True, None


def gather_args(debug=False):

    arg_parser = ArgumentParser(
        formatter_class=RawTextHelpFormatter,
        prog="CHLOE.exe",
        description="Recursively searches a directory of files for a given value.",
        epilog=f"""
=======================

### Usage examples

Searching for the word "test" in this dir.

    {Fore.CYAN}CHLOE.exe --search_terms test

{Fore.RESET}Searching for the word "test" and "phrase" in  a specified dir.

    {Fore.CYAN}CHLOE.exe path/to/dir --search_terms test run

{Fore.RESET}Searching for the word "java" in this dir, avoiding dirs named ".git" and "target".

    {Fore.CYAN}CHLOE.exe --search_terms java --dirs_to_avoid ".git" target

{Fore.RESET}Searching for the phrase "Who Framed Roger Rabbit?" in this dir, saving the output to a file.

    {Fore.CYAN}CHLOE.exe --search_terms "Who Framed Roger Rabbit?" --output File

{Fore.RESET}Searching for the phrase "test example" in .xml and .html files in this dir.

    {Fore.CYAN}CHLOE.exe --search_terms "test example" --target_exts .xml .html
{Fore.RESET}
""",
    )

    arg_parser.add_argument(
        "search_loc",
        type=Path,
        nargs="?",
        default=Path("."),
        help="The location to search",
    )

    arg_parser.add_argument(
        "--search_terms", nargs="+", help="The terms to search for."
    )

    arg_parser.add_argument(
        "--dirs_to_avoid", nargs="*", help="Directories to avoid searching."
    )

    arg_parser.add_argument(
        "--output",
        choices=OUTPUT_CHOICES,
        default=OUTPUT_PRINT,
        help="How to provide the results.",
    )

    arg_parser.add_argument(
        "--target_exts", nargs="*", help="The target file extensions to look for."
    )

    arg_parser.add_argument(
        "--exts_to_avoid", nargs="*", help="The target file extensions to avoid."
    )

    arg_parser.add_argument(
        "--num_futures_in_batch",
        nargs="?",
        type=int,
        default=50,
        help="The number of futures allowed in a group before pausing to resolve them.",
    )

    arg_parser.add_argument(
        "--num_files_in_batch",
        nargs="?",
        type=int,
        default=100,
        help="The max number of files in each processing batch.",
    )

    arg_parser.add_argument(
        "--num_processes",
        nargs="?",
        type=int,
        default=cpu_count(),
        help="The number of processes to use when processing batches.",
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
