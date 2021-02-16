import json
import traceback

import file_utils


class FileProcessor:
    @staticmethod
    def yield_files_with_terms(files, search_terms,case_insensitive):

        for file in files:

            try:

                file_content = str(open(file, "rb").read()).strip()

                for search_term in search_terms:

                    if (case_insensitive and search_term.upper() in file_content.upper()) or (search_term in file_content):

                        yield search_term, file

            except Exception as e:

                yield e, file

    @staticmethod
    def process_files(tmp_dir, files, search_terms, do_add_line_num,case_insensitive):

        try:

            results = {search_term: [] for search_term in search_terms}

            errors = {}

            for search_term, file in FileProcessor.yield_files_with_terms(
                files, search_terms,case_insensitive
            ):

                if isinstance(search_term, Exception):

                    errors[file.__str__()] = search_term.__str__()

                else:

                    results[search_term].append(file.__str__())

            if any([len(collec) > 0 for collec in [results, errors]]):

                filename = file_utils.determine_file_name(tmp_dir)

                if results:

                    if do_add_line_num:

                        results = FileProcessor.add_line_num_to_results(results,case_insensitive)

                    with open(filename, "w+") as out_file:

                        out_file.write(json.dumps(results))

                if errors:

                    with open(filename.with_suffix(".error"), "w+") as out_file:

                        out_file.write(json.dumps(errors))

                return filename

        except:

            traceback.print_exc()

    @staticmethod
    def add_line_num_to_results(results,case_insensitive):

        new_results = {search_term: {} for search_term in set(results.keys())}

        file_search_terms = {}

        for search_term, files in results.items():

            for file in files:

                if file not in file_search_terms.keys():
                    file_search_terms[file] = set()

                file_search_terms[file].add(search_term)

        for file, search_terms in file_search_terms.items():

            for search_term, line_num in FileProcessor.yield_lines_with_search_terms(
                file, search_terms,case_insensitive
            ):

                if file not in new_results[search_term].keys():

                    new_results[search_term][file] = []

                new_results[search_term][file].append(line_num)

        return new_results

    @staticmethod
    def yield_lines_with_search_terms(file, search_terms,case_insensitive):

        with open(file, "rb") as in_file:

            for idx, line in enumerate(in_file):

                for search_term in search_terms:

                    if (case_insensitive and search_term.upper() in str(line).upper()) or (search_term in str(line)):

                        yield search_term, idx + 1
