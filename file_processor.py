import json
import traceback

import pandas as pd

import file_utils


class FileProcessor:

    CASE_SENSITIVE_MATCH = lambda term, content: term in content

    CASE_INSENSITIVE_MATCH = lambda term, content: term.upper() in content.upper()

    @staticmethod
    def yield_files_with_terms(files, search_terms, case_insensitive):

        match_func = FileProcessor.CASE_INSENSITIVE_MATCH if case_insensitive else FileProcessor.CASE_SENSITIVE_MATCH

        for file in files:

            try:

                file_content = str(open(file, "rb").read()).strip()

                for search_term in search_terms:

                    if match_func(search_term,file_content):

                        yield search_term, file

            except Exception as e:

                yield e, file

    @staticmethod
    def process_files(tmp_dir, files, search_terms, do_add_line_num, case_insensitive):

        try:

            results = pd.DataFrame({'Search Term':[],'Path':[]})

            errors = pd.DataFrame({'Error':[],'Path':[]})

            for search_term, file in FileProcessor.yield_files_with_terms(
                files, search_terms, case_insensitive
            ):

                if isinstance(search_term, Exception):

                    errors.loc[len(errors)] = [search_term.__str__(),file.__str__()]

                else:

                    results.loc[len(results)] = [search_term.__str__(),file.__str__()]

            if any([not df.empty for df in [results, errors]]):

                filename = file_utils.determine_file_name(tmp_dir)

                if not results.empty:

                    if do_add_line_num:

                        results = FileProcessor.add_line_num_to_results(
                            results, case_insensitive
                        )

                    results.to_feather(filename)

                if not errors.empty:

                    errors.to_feather(filename.with_suffix(".error"))

                return filename

        except:

            traceback.print_exc()

    @staticmethod
    def add_line_num_to_results(results, case_insensitive):

        new_results = pd.DataFrame({'Search Term':[],'Path':[], 'Line Number':[]})

        for file, search_terms in results.groupby('Path').groups.items():

            for search_term, line_num in FileProcessor.yield_lines_with_search_terms(
                file, list(search_terms), case_insensitive
            ):

                new_results.loc[len(new_results)] = [search_term,file.__str__(),line_num]

        return new_results

    @staticmethod
    def yield_lines_with_search_terms(file, search_terms, case_insensitive):

        match_func = FileProcessor.CASE_INSENSITIVE_MATCH if case_insensitive else FileProcessor.CASE_SENSITIVE_MATCH    

        with open(file, "rb") as in_file:

            for idx, line in enumerate(in_file):

                for search_term in search_terms:

                    if match_func(search_term,line):

                        yield search_term, idx + 1
