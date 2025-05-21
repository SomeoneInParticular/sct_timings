import csv
import logging
from pathlib import Path
from subprocess import run as sh_run
from tempfile import TemporaryDirectory

from setup import setup_sct_bin


def run_deepseg(in_path: Path, out_tsv: Path, deepseg_task: str):
    # Gee Nifty, how come your specification lets you have two extensions?
    scaling = float(in_path.name.split('.nii')[0])
    # Run the subshell in a temporary directory
    with TemporaryDirectory() as tmp:
        out_file = Path(str(tmp)) / "tmp.nii.gz"
        logging.info(f"Running z-axis analysis on {in_path.name}")
        sh_out = sh_run([
            "sct_deepseg", deepseg_task,
            "-i", str(in_path),
            "-o", str(out_file)
        ], capture_output=True)
    # Get the runtime from the log
    runtime_report = sh_out.stdout.decode("utf-8").split('\n')[-2]
    runtime_seconds = float(runtime_report.split("runtime; ")[-1].split(" seconds")[0])
    # Save the result to our file
    with open(out_tsv, 'a') as fp:
        z_tsv = csv.writer(fp, delimiter='\t')
        z_tsv.writerow([scaling, runtime_seconds])


def run_z_tests(data_path: Path, result_path: Path, deepseg_task: str):
    z_out_file = result_path / "z.tsv"
    result_path.mkdir(parents=True, exist_ok=True)

    if z_out_file.exists():
        z_out_file.unlink()

    with open(z_out_file, 'w') as fp:
        z_tsv = csv.writer(fp, delimiter='\t')
        z_tsv.writerow(['Scaling', 'Runtime'])

    # Run the analysis on each of our z-ratio files
    source_path = data_path / "z_ratios"
    for p in source_path.glob('*.nii.gz'):
        run_deepseg(p, z_out_file, deepseg_task)


def run_xy_tests(data_path: Path, result_path: Path, deepseg_task: str):
    xy_out_file = result_path / "xy.tsv"
    result_path.mkdir(parents=True, exist_ok=True)

    if xy_out_file.exists():
        xy_out_file.unlink()

    with open(xy_out_file, 'w') as fp:
        xy_tsv = csv.writer(fp, delimiter='\t')
        xy_tsv.writerow(['Scaling', 'Runtime'])

    # Run the analysis on each of our z-ratio files
    source_path = data_path / "xy_ratios"
    for p in source_path.glob('*.nii.gz'):
        run_deepseg(p, xy_out_file, deepseg_task)


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

    return parser


def main(sct_bin: Path, data_path: Path, result_path: Path, task: str):
    # Ensure everything we want logged is logged
    logging.root.setLevel("INFO")
    # Set up our SCT bin again
    setup_sct_bin(sct_bin)
    # Run the z-level tests
    run_z_tests(data_path, result_path, task)
    # Run the xy-level tests
    run_xy_tests(data_path, result_path, task)


# TODO: Running everything in series is shitty, write a GitHub CI to run it in parallel
if __name__ == '__main__':
    cli_parser = get_parser()
    argvs = cli_parser.parse_args().__dict__
    main(**argvs)
