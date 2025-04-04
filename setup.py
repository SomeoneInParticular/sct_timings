import logging
import os
from pathlib import Path
from shutil import rmtree
from subprocess import run as sh_run
from urllib import request
from zipfile import ZipFile


def setup_sct_bin(sct_bin: Path):
    if not sct_bin.exists():
        raise ValueError(f"Provided `sct_bin` directory '{sct_bin}' does not exist!")
    elif not sct_bin.is_dir():
        raise ValueError(f"Provided `sct_bin` path '{sct_bin}' was not a directory!")

    current_path = os.environ['PATH']
    os.environ['PATH'] = f"{current_path}:{sct_bin}"


def download_data(output_dir, output_file) -> Path:
    # If the output source already exists, skip this step
    logging.info("Grabbing source file!")
    if output_file.exists():
        logging.info("Source file already exists, skipping downloading")
        return output_file

    output_dir.mkdir(exist_ok=True, parents=True)
    zip_file = output_dir / "source.zip"
    request.urlretrieve(
        "https://github.com/spinalcordtoolbox/sct_tutorial_data/releases/download/r20250310/data_spinalcord-segmentation.zip",
        zip_file
    )
    # Extract the archive, and isolate the NIFTI file
    zip_out = output_dir / "zip_data"
    with ZipFile(zip_file, 'r') as zfp:
        zfp.extractall(zip_out)
    zip_file.unlink()  # Clean up
    # If the tutorial ever decides to include multiple files, just take the first one
    nifti_files = list(output_dir.glob("**/*.nii.gz"))
    nifti_files[0].rename(output_file)
    rmtree(zip_out)  # Clean up

    return output_file


def prepare_reference(init_file: Path, data_path: Path):
    # Find the spinal cord centerline
    centerline_cmd = "sct_get_centerline"
    init_name = init_file.name.split('.')[0]
    out_prefix = str(data_path / init_name)
    centerline_out = Path(out_prefix + "_centerline.nii.gz")

    # Generate a centerline, if it doesn't already exist
    if not centerline_out.exists():
        logging.info("Calculating the centerline of the source sequence for use in straightening")
        sh_run([
            centerline_cmd,
            "-i", str(init_file),
            "-c", "t2"
        ])
    else:
        logging.info("Using existing centerline")

    # Straighten the spinal cord to allow for more uniform resolution tests later
    straighten_cmd = "sct_straighten_spinalcord"
    straighten_out = Path(out_prefix + "_straight.nii.gz")
    # Generate the straightened spine, if it doesn't already exist
    if not straighten_out.exists():
        logging.info("Calculating the straightened image for use in cropping")
        sh_run([
            straighten_cmd,
            "-i", str(init_file),
            "-s", str(centerline_out),
            "-ofolder", str(data_path)
        ])
    else:
        logging.info("Using existing straightened spinal cord.")

    # Crop the straighened spinal cord to a standard resolution
    crop_cmd = "sct_crop_image"
    crop_out = Path(out_prefix + "_straight_crop.nii.gz")
    # Generate the straightened spine, if it doesn't already exist
    if not crop_out.exists():
        logging.info("Calculating the cropped image")
        sh_run([
            crop_cmd,
            "-i", str(straighten_out),
            # The below ensures a 64x64x256 voxel sequence
            "-xmin", "0",
            "-xmax", "64",
            "-ymin", "12",
            "-ymax", "76",
            "-zmin", "0",
            "-zmax", "256"
        ])
    else:
        logging.info("Using existing cropped spinal cord.")

    return crop_out


def generate_z_axis_resamples(in_file, out_dir, sampling_ratios):
    # Setup
    resample_cmd = "sct_resample"
    z_out = out_dir / "z_ratios"
    z_out.mkdir(exist_ok=True, parents=True)

    for sr in sampling_ratios:
        sr_str = f"{sr:.3}"
        z_out_file = z_out / f"{sr_str}.nii.gz"
        if z_out_file.exists():
            logging.info(f"File '{str(z_out_file)}' already exists, skipping")
            continue
        sh_run([
            resample_cmd,
            "-i", str(in_file),
            "-o", z_out_file,
            "-f", f"1x1x{sr_str}"
        ])


def generate_xy_axis_resamples(in_file, out_dir, sampling_ratios):
    # Setup
    resample_cmd = "sct_resample"
    xy_out = out_dir / "xy_ratios"
    xy_out.mkdir(exist_ok=True, parents=True)

    for sr in sampling_ratios:
        sr_str = f"{sr:.3}"
        xy_out_file = xy_out / f"{sr_str}.nii.gz"
        if xy_out_file.exists():
            logging.info(f"File '{str(xy_out_file)}' already exists, skipping")
            continue
        sh_run([
            resample_cmd,
            "-i", str(in_file),
            "-o", xy_out_file,
            "-f", f"{sr_str}x{sr_str}x1"
        ])


def get_parser():
    # We only ever need the argument parser when calling this function directly, so import ArgumentParser here
    from argparse import ArgumentParser
    parser = ArgumentParser(
        description="Sets up the workspace for time-based testing of a designated SCT installation"
    )

    parser.add_argument(
        '-s', '--sct_bin', required=True, type=Path,
        help="Path to the SCT bin directory for the SCT version you want to test."
    )

    parser.add_argument(
        '-d', '--data_path', type=Path, default="./data",
        help="Where the imaging data which will be used for the analysis is stored."
    )

    return parser


def main(sct_bin: Path, data_path: Path):
    # Set up the script
    logging.root.setLevel("INFO")

    # Resolve the full path name of the data dir, as some older version of ZIP don't do it for us
    data_path = data_path.resolve()

    # Define where the final source file should be placed
    source_file = data_path / "source.nii.gz"

    # Add the SCT bin to our PATH, saving us some pain later
    setup_sct_bin(sct_bin)

    # Download the data, if it doesn't already exist
    download_data(data_path, source_file)

    # Prepare it by cropping it to a know 32x32x128 range
    reference_file = prepare_reference(source_file, data_path)

    # Resample the reference file along the z-axis and xy-plane
    under_sampling = [.1 * x for x in range(1, 10)]
    over_sampling = [float(2 ** x) for x in range(4)]
    sampling_range = [*under_sampling, *over_sampling]
    generate_z_axis_resamples(reference_file, data_path, sampling_range)
    generate_xy_axis_resamples(reference_file, data_path, sampling_range)


if __name__ == "__main__":
    cli_parser = get_parser()
    argvs = cli_parser.parse_args().__dict__
    main(**argvs)