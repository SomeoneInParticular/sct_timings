# DeepSeg Runtime Estimation

This repo acts as a means to evaluate the runtime of the `deepseg` utility provided by the [Spinal Cord Toolbox](https://spinalcordtoolbox.com/stable/index.html), allowing users to estimate the approximate time required to run an analysis.

## Requirements

* Python 3.7 or newer
* A working installation of Spinal Cord Toolbox

## Running Locally [For Developers]

These instructions detail how to run this analysis on a local Linux computer. We recommend not actually doing this for real analyses, and instead relying on GitHub's CI to run things for you for all platforms (detail in the prior section).

### Preparing to run

1. Find and copy the path to your SCT install bin (i.e. `/user_name/spinalcordtoolbox/bin`); this path will be referred to as `sct_bin_path` from here on.
   * If on Linux/macOS, you can find this with the `which sct_testing` command.
1. Run `setup.py`.
   * This downloads a file, and resamples it a number of times to standardize our estimates. This can take a while!
   ```bash
   python setup.py -s {sct_bin_path} 
   ```

### Running the tool

1. Decide on the `deepseg` task you want to evaluate; this is denoted as the `task_id` in code snippets below.
   * You can get a list of available tasks by calling `sct_deepseg -list-tasks`
1. Run `run.py` and let it complete
   * How long this takes depends substantially on the model being used, and how many replicates (`{no_replicates}`) you request; be patient!
   ```bash
   python run.py -s {sct_bin_path} -t {task_id} -n {no_replicates}
   ```

### Plotting the results
1. Activate the SCT environment provided by your SCT installation.
   * Note that is not the same as `sct_bin_path`, though in most SCT installations you can find it by going up a directory from there and into `python/envs/venv_sct`:
   ```bash
   source activate {sct_bin_path}/../python/envs/venv_sct
   ```
1. Run `plot_results.py`, pointing it towards the result file you want (denoted `{result_file}`) and a filename for the resulting plot (denoted `{plot_file}`)
   ```bash
   python plot_results.py -i {result_file} -o {plot_file}
   ```
