import json
from pathlib import Path
import tempfile
import time
from multiprocessing import Pool, freeze_support
import traceback
import uuid
from sys import exit

import colorama
from colorama import Fore, Back, Style
from tqdm import tqdm

from file_processor import FileProcessor
import file_utils
import output_utils
import args_utils


DO_DEBUG = False


def yield_completed_futures(futures):

    pbar = tqdm(total=len(futures), leave=False)

    while len(futures) > 0:

        futures_to_remove = []

        for future in futures:

            if future.ready():

                yield future

                futures_to_remove.append(future)

                pbar.update(1)

        for future in futures_to_remove:

            futures.remove(future)

    pbar.close()


def resolve_futures(futures, results_path, errors_path):

    pbar_results = tqdm(desc="# New Results", leave=False)

    pbar_error = tqdm(desc='# Errors',leave=False)

    for future in yield_completed_futures(futures):

        filename = future.get()

        if filename is not None:

            error_file = filename.with_suffix(".error")

            for target_file, target_pbar, target_results_path in [[filename,pbar_results,results_path],[error_file,pbar_error,errors_path]]:

                if target_file.exists():

                    num_new_results = file_utils.save_results(target_file, target_results_path)

                    target_pbar.update(num_new_results)

                    target_file.unlink()

    for pbar in [pbar_results, pbar_error]: pbar.close()

def print_banner():

    print(
        f"""{Fore.CYAN}

   ___ _  _ _    ___  ___ 
  / __| || | |  / _ \| __|
 | (__| __ | |_| (_) | _| 
  \___|_||_|____\___/|___|
                          
{Fore.YELLOW}searCH fiLes fOr valuE{Fore.RESET}
"""
    )


if __name__ == "__main__":

    freeze_support()

    start_time = time.time()

    num_batches = 0

    num_files = 0

    try:

        colorama.init()

        print_banner()

        args = args_utils.gather_args(debug=DO_DEBUG)

        with tempfile.TemporaryDirectory() as tmp_dir:

            results_path = Path(tmp_dir).joinpath(uuid.uuid4().__str__())

            errors_path = results_path.with_name("_error")

            print("Temp Dir: " + tmp_dir)

            with Pool(processes=args.processes) as pool:

                futures = []

                for files in file_utils.yield_file_batches(args):

                    num_batches += 1

                    num_files += len(files)

                    futures.append(
                        pool.apply_async(
                            FileProcessor.process_files,
                            (
                                tmp_dir,
                                files,
                                args.search_terms,
                                args.line_num,
                                args.case_insensitive,
                            ),
                        )
                    )

                    if len(futures) == args.max_futures:

                        resolve_futures(futures, results_path, errors_path)

                        futures = []

                resolve_futures(futures, results_path, errors_path)

            output_utils.provide_output(args, results_path, errors_path)

    except Exception as e:

        traceback.print_exc()

    output_utils.print_runtime(start_time, num_batches, num_files, args.processes)
