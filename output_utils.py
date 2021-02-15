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

FORMAT_TABLE = "Table"

FORMAT_DESC = "Desc"

FORMAT_TYPES = [FORMAT_TABLE, FORMAT_DESC]


def determine_output_func(args):

    if args.output == OUTPUT_FILE:

        out_file_path = file_utils.generate_out_file_path(args)

        print("### Results will be saved to " + out_file_path.__str__())

        out_file = open(out_file_path, "w+")

        atexit.register(file_utils.flush_and_close_file, out_file)

        return out_file.write, out_file_path

    else:

        return print, None


def write_descriptive_output(args, results_path, errors_path, output_func):

    if errors_path.exists():

        error_results = json.loads(open(errors_path).read())

        output_func(
            f"### {len(error_results)} files could not be searched due to errors while trying to read their content. ###\n"
        )

        # TODO file paths in the exception string may miscontrue results.
        error_freqs = dict(Counter(list(error_results.values())).most_common())

        median = statistics.median(error_freqs.values())

        output_func("Here's some general stats about the error frequencies:\n")

        median_val = statistics.median(error_freqs.values())

        output_func(
            f"""

    Mean:   {statistics.mean(error_freqs.values())}
    Median: {median_val}
    Mode:   {statistics.mode(error_freqs.values())}

"""
        )

        output_func(
            f"Here's a list of the errors with a frequency >= the median value ({statistics.median(error_freqs.values())}):\n"
        )

        for error, freq in error_freqs.items():

            if freq > median_val:
                output_func(f"\t[{freq}] {error}\n")

        output_func(
            "Here's a complete list of the files and the errors that occured:\n"
        )

        for filename, error in error_results.values():

            output_func(f"{filename} : {error}\n")

    results = json.loads(open(results_path).read()) if results_path.exists() else {}

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

    else:

        output_func("None of the provided search terms were found in any of the files.")


def write_tabular_output(args, results_path, errors_path, output_func, out_path):

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


def provide_output(args, results_path, errors_path):

    output_func, out_path = determine_output_func(args)

    if args.out_format == FORMAT_DESC:

        write_descriptive_output(args, results_path, errors_path, output_func)

    else:

        write_tabular_output(args, results_path, errors_path, output_func, out_path)


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
