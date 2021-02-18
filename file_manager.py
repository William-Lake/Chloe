from datetime import datetime
import json
import os
from pathlib import Path
import uuid

import pandas as pd
from tqdm import tqdm

class FileManager:

    DEFAULT_TARGET_EXTS = ['*']

    def __init__(self,args):

        self._target_exts = self._determine_exts(args.target_exts,self.DEFAULT_TARGET_EXTS)

        self._exts_to_avoid = self._determine_exts(args.exts_to_avoid,[])   

        self._dirs_to_avoid = args.dirs_to_avoid if args.dirs_to_avoid is not None else []  

    def yield_file_batches(self,args):

        files = []

        for file in self._yield_files(args.search_loc):

            files.append(file)

            if len(files) >= args.max_files:

                yield files

                files = []

        if files:

            yield files

    def _yield_files(self,root_dir):

        # I find that os.scandir is faster than pathlib.Path.glob
        for file in tqdm(os.scandir(root_dir.__str__()), leave=False, desc=root_dir.name):

            file = Path(file.path)

            if file.is_dir():

                yield from self._yield_files(file)

            if self._do_yield_file(file):

                yield file

    def _do_yield_file(self,file):

        no_parent_dirs_in_dirs_to_avoid = lambda file: not any([dir.name in file.parts for dir in self._dirs_to_avoid])

        file_ext_not_in_exts_to_avoid = lambda file: not file.suffix in self._exts_to_avoid

        file_has_target_ext = lambda file: self._target_exts == self.DEFAULT_TARGET_EXTS or file.suffix in self._target_exts

        checks = [
            no_parent_dirs_in_dirs_to_avoid,
            file_ext_not_in_exts_to_avoid,
            file_has_target_ext
        ]

        return all([
            check(file)
            for check
            in checks
        ])

    def _determine_exts(self,exts,default_val):

        if not exts:

            return default_val

        else:

            return [
                "." + ext if ext[0] != "." else ext for ext in exts
            ]

    def save_results(self,filename, save_loc):

        og_results = (
            pd.read_feather(save_loc) if save_loc.exists() else None
        )

        new_results = pd.read_feather(filename)

        if og_results is None:

            og_results = new_results

        else:

            og_results = pd.concat([og_results,new_results],ignore_index=True)

        og_results.to_feather(save_loc)

        return len(new_results)

    @staticmethod
    def determine_file_name(parent_dir):

        file_name = None

        while file_name is None:

            file_name = uuid.uuid4().__str__()

            file_name = Path(parent_dir).joinpath(file_name)

            file_name = None if file_name.exists() else file_name

        return file_name

    @staticmethod
    def generate_out_file_path(args):

        if args.out_file is not None:

            return args.out_file.with_suffix(".csv")

        else:

            date_str = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")

            file_name = f"File_Search_Results_{date_str}.csv"

            return Path(file_name).with_suffix(".csv")












