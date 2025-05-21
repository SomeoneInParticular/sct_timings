import csv
import logging
from pathlib import Path
from subprocess import run as sh_run
from tempfile import TemporaryDirectory

from setup import setup_sct_bin


def run_deepseg(in_path: Path, deepseg_task: str):
    # Run the subshell in a temporary directory
    with TemporaryDirectory() as tmp:
        out_file = Path(str(tmp)) / "tmp.nii.gz"
        sh_out = sh_run([
            "sct_deepseg", deepseg_task,
            "-i", str(in_path),
            "-o", str(out_file)
        ], capture_output=True)
    # Get the runtime from the log
    runtime_report = sh_out.stdout.decode("utf-8")
    runtime_seconds = float(runtime_report.split("runtime; ")[-1].split(" seconds")[0])
    return runtime_seconds


def iterative_replicate_run(deepseg_task: str, n: int, source_path: Path, out_file: Path):
    """
    Runs the deepseg task
    :param deepseg_task: The `sct_deepseg` task which should be run
    :param n: The number of replicates which should be run
    :param source_path: The source of MRI sequences which should be iterated through
    :param out_file: The location of the output file that the results should be written too
    :return: None
    """
    for p in source_path.glob('*.nii.gz'):
        # Gee Nifty, how come your specification lets you have two extensions?
        scaling = float(p.name.split('.nii')[0])
        for i in range(n):
            logging.info(f"Running analysis on {p} [replicate {i}]")
            runtime = run_deepseg(p, deepseg_task)
            # Save the result to our file
            with open(out_file, 'a') as fp:
                out_tsv = csv.writer(fp, delimiter='\t')
                out_tsv.writerow([scaling, i, runtime])


def init_results_file(result_file):
    # Initiate the results file with a set of standard headers
    with open(result_file, 'w') as fp:
        xy_tsv = csv.writer(fp, delimiter='\t')
        xy_tsv.writerow(['Scaling', 'Replicate', 'Runtime'])


def run_z_tests(data_path: Path, result_path: Path, deepseg_task: str, n: int):
    # Reset the existing results file if it already exists
    z_out_file = result_path / "z.tsv"
    result_path.mkdir(parents=True, exist_ok=True)

    if z_out_file.exists():
        z_out_file.unlink()

    init_results_file(z_out_file)

    # Run the analysis on each of our z-ratio files, n times
    source_path = data_path / "z_ratios"
    iterative_replicate_run(deepseg_task, n, source_path, z_out_file)


def run_xy_tests(data_path: Path, result_path: Path, deepseg_task: str, n: int):
    # Reset the existing file if it already exists
    xy_out_file = result_path / "xy.tsv"
    result_path.mkdir(parents=True, exist_ok=True)

    if xy_out_file.exists():
        xy_out_file.unlink()

    # Initialize the results file
    init_results_file(xy_out_file)

    # Run the analysis on each of our z-ratio files, n times
    source_path = data_path / "xy_ratios"
    iterative_replicate_run(deepseg_task, n, source_path, xy_out_file)


def get_parser():
    # We only ever need the argument parser when calling this function directly, so import ArgumentParser here
    from argparse import ArgumentParser
    parser = ArgumentParser(
        description="Runs a DeepSeg analysis repeatedly on several MRI sequence resolutions, recording their runtime "
                    "each time."
    )

    parser.add_argument(
        '-s', '--sct_bin', required=True, type=Path,
        help="Path to the SCT bin directory for the SCT version you want to test."
    )
    parser.add_argument(
        '-t', '--task', required=True, type=str,
        help="The DeepSeg task to run. Valid options are the same as those produced by `deepseg -list-tasks`."
    )

    parser.add_argument(
        '-d', '--data_path', type=Path, default="./data",
        help="Where the imaging data which will be used for the analysis is stored."
    )
    parser.add_argument(
        '-r', '--result_path', type=Path, default="./results",
        help="Where the timing results of this analysis will be saved."
    )
    parser.add_argument(
        '-n', '--no_replicates', type=int, default=10,
        help="Number of replicates runs for each testing file. "
             "Higher results in a longer run time, but is more robust to changes in resource availability."
    )

    return parser


def main(sct_bin: Path, data_path: Path, result_path: Path, task: str, no_replicates: int):
    # Ensure everything we want logged is logged
    logging.root.setLevel("INFO")
    # Set up our SCT bin again
    setup_sct_bin(sct_bin)
    # Run the z-level tests
    run_z_tests(data_path, result_path, task, no_replicates)
    # Run the xy-level tests
    run_xy_tests(data_path, result_path, task, no_replicates)


# TODO: Running everything in series is shitty, write a GitHub CI to run it in parallel
if __name__ == '__main__':
    cli_parser = get_parser()
    argvs = cli_parser.parse_args().__dict__
    main(**argvs)
