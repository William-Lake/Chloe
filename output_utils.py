import atexit
from collections import Counter
import json
from pathlib import Path
import statistics
import time

import pandas as pd

import file_utils

OUTPUT_FILE = "File"

OUTPUT_PRINT = "Print"

OUTPUT_CHOICES = [OUTPUT_FILE, OUTPUT_PRINT]


def determine_output_func(args):

    if args.output == OUTPUT_FILE:

        out_file_path = file_utils.generate_out_file_path(args)

        print("### Results will be saved to " + out_file_path.__str__())

        out_file = open(out_file_path, "w+")

        atexit.register(file_utils.flush_and_close_file, out_file)

        return out_file.write, out_file_path

    else:

        return print, None

def provide_output(args, results_path, errors_path):

    output_func, out_path = determine_output_func(args)

    if errors_path.exists():

        error_results = json.loads(open(errors_path).read())

        error_df = pd.DataFrame({"Path": [], "Error": []})

        for path, error in error_results.items():

            error_df.loc[len(error_df)] = [path, error]

        if out_path is not None:

            error_out_path = out_path.with_name(out_path.stem + "_error").with_suffix(
                ".csv"
            )

            print(f"Saving errors to {error_out_path.__str__()}")

            error_df.to_csv(error_out_path, index=False)

        else:

            output_func(error_df.to_string())

    results = json.loads(open(results_path).read()) if results_path.exists() else {}

    if any([len(val) > 0 for val in results.values()]):

        if isinstance(list(results.values())[0], list):

            results_df = pd.DataFrame({"Search Term": [], "Path": []})

            for search_term, locations in results.items():

                for loc in locations:

                    results_df.loc[len(results_df)] = [search_term, loc]

            if out_path is not None:

                results_df.to_csv(out_path, index=False)

            else:

                output_func(results_df.to_string())

        else:

            results_df = pd.DataFrame({"Search Term": [], "Path": [], "Line #": []})

            for search_term, locations in results.items():

                for loc, line_nums in locations.items():

                    results_df.loc[len(results_df)] = [search_term, loc, line_nums]

            if out_path is not None:

                results_df.to_csv(out_path, index=False)

            else:

                output_func(results_df.to_string())

    else:

        output_func("None of the provided search terms were found in any of the files.")


def print_runtime(start_time):

    time_in_seconds = time.time() - start_time

    time_in_minutes = time_in_seconds / 60

    time_in_hours = time_in_minutes / 60

    total_time, time_label = (
        (time_in_hours, "hours") if time_in_hours >= 1 else (time_in_minutes, "minutes")
    )

    if total_time < 1:
        total_time, time_label = (time_in_seconds, "seconds")

    print(f"Total runtime: {total_time:.2f} {time_label}.")
