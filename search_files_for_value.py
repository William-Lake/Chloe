import json
from pathlib import Path
import tempfile
import time
from multiprocessing import Pool, freeze_support
import traceback
import uuid
from sys import exit

import colorama
from colorama import Fore, Back, Style
from tqdm import tqdm

import output_utils
import args_utils
from chloe import Chloe


DO_DEBUG = False


def main(args):

    output_utils.print_banner() 

    try:

        start_time = time.time()

        chloe = Chloe()

        with tempfile.TemporaryDirectory() as tmp_dir:

            chloe.start(args,tmp_dir)

            output_utils.provide_output(args, chloe.results_path, chloe.errors_path)

            output_utils.print_runtime(start_time, chloe.num_batches, chloe.num_files, args.processes)

    except:

        traceback.print_exc()     


if __name__ == "__main__":

    freeze_support()

    colorama.init()

    args = args_utils.gather_args(debug=DO_DEBUG)

    main(args)
