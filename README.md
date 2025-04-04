# DeepSeg Runtime Estimation

This repo acts as a means to evaluate the runtime of the `deepseg` utility provided by the [Spinal Cord Toolbox](https://spinalcordtoolbox.com/stable/index.html), allowing users to estimate the approximate time required to run an analysis.

## Requirements

* Python 3.7 or newer
* A working installation of Spinal Cord Toolbox

## Preparing to run

1. Find and copy the path to your SCT install bin (i.e. `/user_name/spinalcordtoolbox/bin`); this path will be referred to as `sct_bin_path` from here on.
   * If on Linux/macOS, you can find this with the `which sct_testing` command.
1. Run `setup.py -s {sct_bin_path}`.
   * This downloads a file, and resamples it a number of times to standardize our estimates. This can take a while!

## Running the tool

1. Decide on the `deepseg` task you want to evaluate; this is denoted as the `task_id` in code snippets below.
   * You can get a list of available tasks by calling `sct_deepseg -list-tasks`
1. Run `run.py -s {sct_bin_path} -t {task_id}` and let it complete
   * How long this takes depends substantially on the model being used; be patient!

