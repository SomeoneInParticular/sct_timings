# DeepSeg Runtime Estimation

This repo acts as a means to evaluate the runtime of the `deepseg` utility provided by the [Spinal Cord Toolbox](https://spinalcordtoolbox.com/stable/index.html), allowing users to estimate the approximate time required to run an analysis.

## Requirements

* Python 3.7 or newer
* A working installation of Spinal Cord Toolbox

## Preparing to run

1. Update `config.json` to point to your Spinal Cord Toolbox bin directory (i.e. `/user_name/spinalcordtoolbox/bin`)
   * If on linux, you can find this with the `which sct_testing` command.
1. Run `setup.py`; 
   * This downloads a file, and resamples it a number of times to standardize our estimates. This can take a while!

## Running the tool

1. Specify the `deepseg` task you want evaluated within the `config.json`
1. Run `run.py` and let it complete
   * How long this takes depends substantially on the model being used; be patient!

