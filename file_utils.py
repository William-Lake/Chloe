from datetime import datetime
import json
from pathlib import Path
import uuid

from tqdm import tqdm

from output_utils import FORMAT_DESC


def determine_file_name(tmp_dir):

    file_name = None

    while file_name is None:

        file_name = uuid.uuid4().__str__()

        file_name = Path(tmp_dir).joinpath(file_name)

        file_name = None if file_name.exists() else file_name

    return file_name


def generate_out_file_path(args):

    date_str = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")

    file_name = f"File_Search_Results_{date_str}"

    out_suffix = '.txt' if args.out_format == FORMAT_DESC else '.csv'

    return Path(file_name).with_suffix(out_suffix)


def flush_and_close_file(file):

    file.flush()

    file.close()


def save_results(filename, results_path):

    og_results = (
        json.loads(open(results_path).read()) if results_path.exists() else None
    )

    the_results = json.loads(open(filename).read())

    num_new_results = sum([len(v) for v in the_results.values()])

    if og_results is None:

        og_results = the_results

    else:

        for search_term, target_files in the_results.items():

            if search_term in og_results.keys():

                if isinstance(target_files,list):

                    og_results[search_term].extend(target_files)

                else:

                    for file, line_nums in target_files.items():

                        if file not in og_results[search_term].keys():

                            og_results[search_term][file] = []

                        og_results[search_term][file].append(', '.join(str(line_num) for line_num in line_nums))

            else:

                og_results[search_term] = target_files

    with open(results_path, "w+") as out_file:

        out_file.write(json.dumps(og_results, indent=4))

    return num_new_results


def yield_files(args):

    if not args.target_exts:

        target_exts = ["*"]

    else:

        target_exts = ["." + ext if ext[0] != "." else ext for ext in args.target_exts]

    if not args.exts_to_avoid:

        exts_to_avoid = []

    else:

        exts_to_avoid = [
            "." + ext if ext[0] != "." else ext for ext in args.exts_to_avoid
        ]

    for ext in target_exts:

        for file in tqdm(args.search_loc.glob(f"**/{ext}"), leave=False, desc="Files"):

            if file.is_dir():
                continue

            if args.dirs_to_avoid is not None and any(
                [dir in file.parts for dir in args.dirs_to_avoid]
            ):
                continue

            if file.suffix in exts_to_avoid:
                continue

            yield file


def yield_file_batches(args):

    files = []

    pbar = tqdm(desc="File Batches", leave=False)

    for file in yield_files(args):

        files.append(file)

        if len(files) >= args.num_files_in_batch:

            pbar.update(1)

            yield files

            files = []

    if files:

        pbar.update(1)

        yield files

    pbar.close()
