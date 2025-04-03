import csv
import logging
from json import load
from pathlib import Path
from subprocess import run as sh_run
from tempfile import TemporaryDirectory

from setup import setup_sct_bin


def get_config_vals():
    with open("config.json", 'r') as fp:
        config_vals = load(fp)

    return config_vals


def run_z_tests():
    z_out_file = Path("results/z.tsv")
    z_out_file.parent.mkdir(parents=True, exist_ok=True)
    if z_out_file.exists():
        z_out_file.unlink()
    with open(z_out_file, 'w') as fp:
        z_tsv = csv.writer(fp, delimiter='\t')
        z_tsv.writerow(['Scaling', 'Runtime'])
    # Run the analysis on each of our z-ratio files
    for p in Path('data/z_ratios').glob('*.nii.gz'):
        # Gee Nifty, how come your specification lets you have two extensions?
        scaling = float(p.name.split('.nii')[0])

        # Run the subshell in a temporary directory
        with TemporaryDirectory() as tmp:
            out_file = Path(str(tmp)) / "tmp.nii.gz"
            logging.info(f"Running z-axis analysis on {p.name}")
            sh_out = sh_run([
                "sct_deepseg", cfg['task'],
                "-i", str(p),
                "-o", str(out_file)
            ], capture_output=True)

        # Get the runtime from the log
        runtime_report = sh_out.stdout.decode("utf-8").split('\n')[-2]
        runtime_seconds = float(runtime_report.split("; ")[-1].split(" s")[0])

        # Save the result to our file
        with open(z_out_file, 'a') as fp:
            z_tsv = csv.writer(fp, delimiter='\t')
            z_tsv.writerow([scaling, runtime_seconds])


def run_xy_tests():
    xy_out_file = Path("results/xy.tsv")
    xy_out_file.parent.mkdir(parents=True, exist_ok=True)
    if xy_out_file.exists():
        xy_out_file.unlink()
    with open(xy_out_file, 'w') as fp:
        xy_tsv = csv.writer(fp, delimiter='\t')
        xy_tsv.writerow(['Scaling', 'Runtime'])
    # Run the analysis on each of our z-ratio files
    for p in Path('data/xy_ratios').glob('*.nii.gz'):
        # Gee Nifty, how come your specification lets you have two extensions?
        scaling = float(p.name.split('.nii')[0])

        # Run the subshell in a temporary directory
        with TemporaryDirectory() as tmp:
            out_file = Path(str(tmp)) / "tmp.nii.gz"
            logging.info(f"Running xy-axis analysis on {p.name}")
            sh_out = sh_run([
                "sct_deepseg", cfg['task'],
                "-i", str(p),
                "-o", str(out_file)
            ], capture_output=True)

        # Get the runtime from the log
        runtime_report = sh_out.stdout.decode("utf-8").split('\n')[-2]
        runtime_seconds = float(runtime_report.split("; ")[-1].split(" s")[0])

        # Save the result to our file
        with open(xy_out_file, 'a') as fp:
            xy_tsv = csv.writer(fp, delimiter='\t')
            xy_tsv.writerow([scaling, runtime_seconds])


# TODO: Running everything in series is shitty, write a GitHub CI to run it in parallel
if __name__ == '__main__':
    # Ensure everything we want logged is logged
    logging.root.setLevel("INFO")

    # Set up our SCT bin again
    setup_sct_bin()

    # Load the config values
    cfg = get_config_vals()

    # Run the z-level tests
    run_z_tests()

    # Run the xy-level tests
    run_xy_tests()
