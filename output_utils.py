import atexit
from collections import Counter
import json
from pathlib import Path
import statistics
import time

from colorama import Fore, Back, Style
import pandas as pd

import file_utils

OUTPUT_FILE = "File"

OUTPUT_PRINT = "Print"

OUTPUT_CHOICES = [OUTPUT_FILE, OUTPUT_PRINT]


def provide_output(args, results_path, errors_path):

    out_path = file_utils.generate_out_file_path(args)

    for df_path,df_name in [[results_path,'Search Results'],[errors_path,'Errors']]:

        if df_path.exists():

            df = pd.read_feather(df_path)

            num_results = len(df)

            print(f'{Fore.CYAN}There were {Fore.MAGENTA}{num_results} {Fore.CYAN}{df_name}.{Fore.RESET}')

            if df.empty: continue

            if args.output == OUTPUT_FILE:

                df_outpath = out_path.with_name(out_path.stem + f"_{df_name}").with_suffix(
                ".csv"
                )

                df.to_csv(df_outpath,index=False)

                print(f'Saved {df_name} to {df_outpath.__str__()}')

            else:

                print(Fore.GREEN + Style.BRIGHT + df.to_string() + Style.RESET_ALL)


def get_time_string_for_time(time_in_seconds):

    time_in_minutes = time_in_seconds / 60

    time_in_hours = time_in_minutes / 60

    total_time, time_label = (
        (time_in_hours, "hours") if time_in_hours >= 1 else (time_in_minutes, "minutes")
    )

    if total_time < 1:
        total_time, time_label = (time_in_seconds, "seconds")

    return f'{total_time:.2f} {time_label}'

def print_runtime(start_time, num_batches, num_files, num_processes):

    time_in_seconds = time.time() - start_time

    total_time_str = get_time_string_for_time(time_in_seconds)

    time_per_batch = (time_in_seconds / num_batches) if num_batches > 0 else time_in_seconds

    time_per_batch = get_time_string_for_time(time_per_batch)

    time_per_file = (time_in_seconds / num_files) if num_files > 0 else time_in_seconds

    time_per_file = get_time_string_for_time(time_per_file)

    print(
        f"""{Fore.CYAN}
###########################################################

    # Processes:       {Fore.MAGENTA}{num_processes}{Fore.CYAN}
    # Batches:         {Fore.MAGENTA}{num_batches}{Fore.CYAN}
    # Files Processed: {Fore.MAGENTA}{num_files}{Fore.CYAN}
    
    Total Runtime:     {Fore.MAGENTA}{total_time_str}{Fore.CYAN}
    Time/Batch:        {Fore.MAGENTA}{time_per_batch}{Fore.CYAN}
    Time/File:         {Fore.MAGENTA}{time_per_file}{Fore.CYAN}

###########################################################
{Fore.RESET}"""
    )
