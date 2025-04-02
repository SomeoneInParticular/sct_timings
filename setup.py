import logging
import os
from json import load
from pathlib import Path
from shutil import rmtree
from urllib import request
from zipfile import ZipFile

from subprocess import run as sh_run


def setup_sct_bin():
    # Get the desired SCT bin and add it to our shell's PATH
    logging.info("Adding SCT install to PATH")

    with open("config.json", 'r') as fp:
        config_vals = load(fp)
    sct_bin = Path(config_vals['sct_bin'])

    if not sct_bin.exists():
        raise ValueError(f"Provided `sct_bin` directory '{sct_bin}' does not exist!")
    elif not sct_bin.is_dir():
        raise ValueError(f"Provided `sct_bin` path '{sct_bin}' was not a directory!")

    current_path = os.environ['PATH']
    os.environ['PATH'] = f"{current_path}:{sct_bin}"


def download_data(output_dir, output_file) -> Path:
    # If the output source already exists, skip this step
    if output_file.exists():
        logging.info("Source file already exists, skipping downloading")
        return output_file

    output_dir.parent.mkdir(exist_ok=True, parents=True)
    zip_file = output_dir / "source.zip"
    request.urlretrieve(
        "https://github.com/spinalcordtoolbox/sct_tutorial_data/releases/download/r20250310/data_spinalcord-segmentation.zip",
        output_dir / "source.zip"
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


def prepare_reference(init_file: Path):
    # Find the spinal cord centerline
    centerline_cmd = "sct_get_centerline"
    centerline_out = Path((str(init_file).split('.')[0] + "_centerline.nii.gz"))
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
    straighten_out = Path((str(init_file).split('.')[0] + "_straight.nii.gz"))
    # Generate the straightened spine, if it doesn't already exist
    if not straighten_out.exists():
        logging.info("Calculating the straightened image for use in cropping")
        sh_run([
            straighten_cmd,
            "-i", str(init_file),
            "-s", str(centerline_out),
            "-ofolder", str(data_dir)
        ])
    else:
        logging.info("Using existing straightened spinal cord.")
    # Crop the straighened spinal cord to a standard resolution
    crop_cmd = "sct_crop_image"
    crop_out = Path((str(straighten_out).split('.')[0] + "_crop.nii.gz"))
    # Generate the straightened spine, if it doesn't already exist
    if not crop_out.exists():
        logging.info("Calculating the cropped image")
        sh_run([
            crop_cmd,
            "-i", str(straighten_out),
            # The below ensures a 32x32x256 voxel sequence
            "-xmin", "16",
            "-xmax", "48",
            "-ymin", "28",
            "-ymax", "60",
            "-zmin", "0",
            "-zmax", "256"
        ])
    else:
        logging.info("Using existing cropped spinal cord.")

    return crop_out


def generate_z_axis_resamples(in_file, out_dir):
    # Resample the image along the z axis to give us a base-2 logarithmic range
    sampling_ratios = [2 ** i for i in range(-2, 3)]
    resample_cmd = "sct_resample"
    z_out = out_dir / "z_ratios"
    z_out.mkdir(exist_ok=True, parents=True)

    for sr in sampling_ratios:
        z_out_file = z_out / f"{sr}.nii.gz"
        if z_out_file.exists():
            logging.info(f"File '{str(z_out_file)}' already exists, skipping")
            continue
        sh_run([
            resample_cmd,
            "-i", str(in_file),
            "-o", z_out_file,
            "-f", f"1x1x{str(sr)}"
        ])


def generate_xy_axis_resamples(in_file, out_dir):
    # Resample the image along the z axis to give us a base-2 logarithmic range
    sampling_ratios = [2 ** i for i in range(-2, 3)]
    resample_cmd = "sct_resample"
    xy_out = out_dir / "xy_ratios"
    xy_out.mkdir(exist_ok=True, parents=True)

    for sr in sampling_ratios:
        xy_out_file = xy_out / f"{sr}.nii.gz"
        if xy_out_file.exists():
            logging.info(f"File '{str(xy_out_file)}' already exists, skipping")
            continue
        sh_run([
            resample_cmd,
            "-i", str(in_file),
            "-o", xy_out_file,
            "-f", f"{str(sr)}x{str(sr)}x1"
        ])


if __name__ == "__main__":
    # Set up the script
    logging.root.setLevel("INFO")
    data_dir = Path("data")
    source_file = data_dir / "source.nii.gz"

    # Add the SCT bin to our PATH, saving us some pain later
    setup_sct_bin()

    # Download the data, if it doesn't already exist
    download_data(data_dir, source_file)

    # Prepare it by cropping it to a know 32x32x128 range
    reference_file = prepare_reference(source_file)

    # Resample the reference file along the z-axis and xy-plane
    generate_z_axis_resamples(reference_file, data_dir)
    generate_xy_axis_resamples(reference_file, data_dir)
