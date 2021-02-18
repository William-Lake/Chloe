import atext


class FutureManager:

    def _create_pbars(self):

        self._pbar_results = tqdm(desc="# New Results", leave=False)

        self._pbar_error = tqdm(desc='# Errors',leave=False)

    def _close_pbars(self):

        self._pbar_results.close()

        self._pbar_error.close()        

    def resolve_futures(self,futures, results_path, errors_path):

        self._create_pbars()

        for future in self._yield_completed_futures(futures):

            yield from self._resolve_future(future)

        self._close_pbars()

    def _resolve_future(self,future,results_path,errors_path):

        filename = future.get()

        if filename is not None:

            error_file = filename.with_suffix(".error")

            for target_file, target_pbar, target_results_path in [[filename,self._pbar_results,results_path],[error_file,self._pbar_error,errors_path]]:

                if target_file.exists():

                    yield target_file, target_pbar, target_results_path

    def _yield_completed_futures(self,futures):

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