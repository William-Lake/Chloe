import json
from pathlib import Path
import uuid
import traceback


class FileProcessor:
    @staticmethod
    def yield_files_with_terms(files, search_terms):

        for file in files:

            try:

                file_content = str(open(file, "rb").read()).strip().upper()

                for search_term in search_terms:

                    if search_term.upper() in file_content.upper():

                        yield search_term, file

            except Exception as e:

                yield e, file

    @staticmethod
    def determine_file_name(tmp_dir):

        file_name = None

        while file_name is None:

            file_name = uuid.uuid4().__str__()

            file_name = Path(tmp_dir).joinpath(file_name)

            file_name = None if file_name.exists() else file_name

        return file_name

    @staticmethod
    def process_files(tmp_dir, files, search_terms):

        try:

            results = {search_term: [] for search_term in search_terms}

            errors = {}

            for search_term, file in FileProcessor.yield_files_with_terms(
                files, search_terms
            ):

                if isinstance(search_term, Exception):

                    errors[file.__str__()] = search_term.__str__()

                else:

                    results[search_term].append(file.__str__())

            if any([len(collec) > 0 for collec in [results, errors]]):

                filename = FileProcessor.determine_file_name(tmp_dir)

                if results:

                    with open(filename, "w+") as out_file:

                        out_file.write(json.dumps(results))

                if errors:

                    with open(filename.with_suffix(".error"), "w+") as out_file:

                        out_file.write(json.dumps(errors))

                return filename

        except:

            traceback.print_exc()

    @staticmethod
    def flush_and_close_file(file):

        file.flush()

        file.close()