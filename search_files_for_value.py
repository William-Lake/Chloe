import atexit
from argparse import ArgumentParser, RawTextHelpFormatter
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import tempfile
import time
from multiprocessing import Pool, freeze_support
import string
import random
import traceback
from sys import exit

import colorama
from colorama import Fore, Back, Style
from tqdm import tqdm


NUM_FILES_IN_BATCH = 100

RESULTS_PATH = Path("v2_results.json")

DO_DEBUG = False

OUTPUT_FILE = "File"

OUTPUT_PRINT = "Print"

OUTPUT_CHOICES = [OUTPUT_FILE, OUTPUT_PRINT]


class FileProcessor:
    @staticmethod
    def collect_file_content(file):

        try:

            return str(open(file, "rb").read())

        except Exception as e:

            print("Exception while reading file.", file, str(e))

    @staticmethod
    def yield_files_with_terms(files, search_terms):

        for file in files:

            file_content = FileProcessor.collect_file_content(file)

            if file_content is None:
                continue

            for search_term in search_terms:

                if search_term in file_content:

                    yield search_term, file

    @staticmethod
    def determine_file_name(tmp_dir):

        while True:

            name = "".join(random.choices(string.ascii_letters, k=20))

            name = Path(tmp_dir).joinpath(f"{name}.json")

            if not name.exists():
                return name

    @staticmethod
    def process_files(tmp_dir, files, search_terms):

        try:

            results = {search_term: [] for search_term in search_terms}

            for search_term, file in FileProcessor.yield_files_with_terms(
                files, search_terms
            ):

                results[search_term].append(file.__str__())

            if results:

                filename = FileProcessor.determine_file_name(tmp_dir)

                with open(filename, "w+") as out_file:

                    out_file.write(json.dumps(results))

                return filename

        except:

            traceback.print_exc()

    @staticmethod
    def flush_and_close_file(file):

        file.flush()

        file.close()


def generate_out_file_path():

    date_str = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")

    file_name = f"File_Search_Results_{date_str}"

    return Path(file_name).with_suffix(".txt")


def determine_output_func(args):

    if args.output == OUTPUT_FILE:

        out_file_path = generate_out_file_path()

        print("### Results will be saved to " + out_file_path.__str__())

        out_file = open(out_file_path, "w+")

        atexit.register(FileProcessor.flush_and_close_file, out_file)

        return out_file.write

    else:

        return print


def provide_output(args):

    results = json.loads(open(RESULTS_PATH).read())

    output_func = determine_output_func(args)

    if any([len(val) > 0 for val in results.values()]):

        for search_term, locations in results.items():

            if not locations:

                output_func(f"{search_term} not found.\n")

                continue

            output_func(f"\n\n{search_term} found in {len(locations)} locations.\n")

            frequency_gathering_functions = {
                "File Types": lambda val: Path(val).suffix,
                "File Names": lambda val: Path(val).name,
                "Parent Folders": lambda val: Path(val).parent.name,
                "Parent Folder/Child File Combo": lambda val: Path(val).parent.joinpath(
                    Path(val).name
                ),
                "Root Folders": lambda val: Path(val)
                .relative_to(args.search_loc)
                .parts[0],
            }

            for freq_type, method in frequency_gathering_functions.items():

                freqs = dict(Counter([method(loc) for loc in locations]))

                freqs = {str(item): count for item, count in freqs.items() if count > 1}

                freqs = dict(sorted(freqs.items(), key=lambda kv: kv[1], reverse=True))

                if freqs:

                    output_func(
                        f"""
###################################

There was a common thread in {freq_type} when searching for {search_term}. The following {freq_type[:-1]} showed up more than once:

{json.dumps(freqs,indent=4)}

"""
                    )

            output_func("Location List\n=============================\n")

            output_func(
                "\n\n\t"
                + "\n\t".join([location.__str__() for location in locations])
                + "\n\n"
            )

        RESULTS_PATH.unlink()

    else:

        output_func("None of the provided search terms were found in any of the files.")


def save_results(filename):

    og_results = (
        json.loads(open(RESULTS_PATH).read()) if RESULTS_PATH.exists() else None
    )

    the_results = json.loads(open(filename).read())

    if og_results is None:

        og_results = the_results

    else:

        for search_term, target_files in the_results.items():

            if search_term in og_results.keys():

                og_results[search_term].extend(target_files)

            else:

                og_results[search_term] = target_files

    with open(RESULTS_PATH, "w+") as out_file:

        out_file.write(json.dumps(og_results, indent=4))


def yield_completed_futures(futures):

    pbar = tqdm(total=len(futures), leave=False)

    sleep_time = (NUM_FILES_IN_BATCH / 10) * 2

    while len(futures) > 0:

        futures_to_remove = []

        for future in futures:

            if future.ready():

                yield future

                futures_to_remove.append(future)

                pbar.update(1)

        for future in futures_to_remove:

            futures.remove(future)

        if len(futures) > 0:

            time.sleep(sleep_time)

    pbar.close()


def yield_files(args):
    
    if not args.target_exts:
        
        target_exts = ['*']
        
    else:
        
        target_exts = [
            '.' + ext if ext[0] != '.' else ext
            for ext
            in args.target_exts
        ]
        
    for ext in target_exts:

        for file in tqdm(args.search_loc.glob(f"**/{ext}"), leave=False, desc="Files"):

            if file.is_dir():
                continue

            if args.dirs_to_avoid is not None and any(
                [dir in file.parts for dir in args.dirs_to_avoid]
            ):
                continue

            yield file


def yield_file_batches(args):

    files = []

    pbar = tqdm(desc='File Batches',leave=False)

    for file in yield_files(args):

        files.append(file)

        if len(files) >= NUM_FILES_IN_BATCH:

            pbar.update(1)

            yield files

            files = []

    if files:

        pbar.update(1)

        yield files

    pbar.close()

def args_acceptable(args):

    search_loc = args.search_loc

    search_terms = args.search_terms

    if not search_loc.exists():

        return False, f'{search_loc.__str__()} could not be found!'

    if search_terms is None:

        search_terms = []

    search_terms = [
        term
        for term
        in search_terms
        if term is not None and len(term.strip()) > 0
    ]

    if not search_terms:

        return False, 'Please provide at least one search term!'

    return True, None

def gather_args(debug=False):

    arg_parser = ArgumentParser(formatter_class=RawTextHelpFormatter,prog='CHLOE.exe',description='Recursively searches a directory of files for a given value.',epilog=f'''
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
''')

    arg_parser.add_argument("search_loc", type=Path, nargs='?', default=Path('.'), help='The location to search')

    arg_parser.add_argument("--search_terms", nargs="+",help='The terms to search for.')

    arg_parser.add_argument("--dirs_to_avoid", nargs="*",help='Directories to avoid searching.')

    arg_parser.add_argument("--output", choices=OUTPUT_CHOICES, default=OUTPUT_PRINT,help='How to provide the results.')
    
    arg_parser.add_argument('--target_exts',nargs='*',help='The target file extensions to look for.')

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

def print_banner():

    print(f'''{Fore.CYAN}

   ___ _  _ _    ___  ___ 
  / __| || | |  / _ \| __|
 | (__| __ | |_| (_) | _| 
  \___|_||_|____\___/|___|
                          
{Fore.YELLOW}searCH fiLes fOr valuE{Fore.RESET}
''')  

if __name__ == "__main__":

    freeze_support()

    try:

        colorama.init()

        print_banner()

        args = gather_args(debug=DO_DEBUG)

        if RESULTS_PATH.exists():
            RESULTS_PATH.unlink()

        with tempfile.TemporaryDirectory() as tmp_dir:

            print(f"Temp Dir: " + tmp_dir)

            with Pool() as pool:

                futures = []

                for files in yield_file_batches(args):

                    futures.append(
                        pool.apply_async(
                            FileProcessor.process_files,
                            (tmp_dir, files, args.search_terms),
                        )
                    )

                for future in yield_completed_futures(futures):

                    filename = future.get()

                    if filename is not None:

                        save_results(filename)

                    filename.unlink()

        if RESULTS_PATH.exists():

            provide_output(args)

    except Exception as e:

        traceback.print_exc()

