from multiprocessing import Pool
from pathlib import Path
import uuid

from tqdm import tqdm

from file_manager import FileManager
from file_processor import FileProcessor
from future_manager import FutureManager



class Chloe:

    def start(self,args,tmp_dir):

        print(f'Temp Dir: {tmp_dir}')

        self._prep(tmp_dir,args)

        with Pool(processes=args.processes) as pool:

            futures = []

            for files in tqdm(self._file_manager.yield_file_batches(args)):

                self.num_batches += 1

                self.num_files += len(files)

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

                    self._resolve_futures(futures)

                    futures = []

            self._resolve_futures(futures) 

    def _resolve_futures(self,futures):   

        for target_file, target_pbar, targetresults_path in self._future_manager.resolve_futures(futures, self.results_path, self.errors_path):

            num_new_results = self._file_manager.save_results(target_file, targetresults_path)

            target_pbar.update(num_new_results)

            target_file.unlink()                  

    def _prep(self,tmp_dir,args):

        self.num_batches = 0

        self.num_files = 0          

        self.results_path = Path(tmp_dir).joinpath(uuid.uuid4().__str__())

        self.errors_path = self.results_path.with_name("_error")    

        self._file_manager = FileManager(args)           

        self._future_manager = FutureManager()