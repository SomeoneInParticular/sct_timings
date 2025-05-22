from pathlib import Path
from typing import Optional

import pandas as pd
from matplotlib import pyplot as plt


def plot_results(df: pd.DataFrame, output_file: Path, title: Optional[str], zoom: bool = False):
    # Initiate the plotting space
    fig, ax = plt.subplots(1, 1)

    plot_data(ax, df)

    # If requested, add a "zoomed-in" inset of sub-1 ratio elements
    if zoom:
        zoomed_subplot(ax, df)

    # Add axis labels
    ax.set_xlabel('Sequence Scaling')
    ax.set_ylabel('Runtime (in Seconds)')

    # If the user provided a title, add it to the plot
    if title:
        ax.set_title(title)

    # Force tight layout, we hate whitespace here
    plt.tight_layout()

    # Save the result
    output_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_file)


def zoomed_subplot(based_ax, df):
    # Based on https://matplotlib.org/stable/gallery/subplots_axes_and_figures/zoom_inset_axes.html # noqa: E501 (I can't exactly make the URL shorter)
    x1, x2 = 0.05, 1.05
    runtimes = df.query('Scaling <= 1')['Runtime']
    y1, y2 = runtimes.min(), runtimes.max()
    zoomed_ax = based_ax.inset_axes(
        (0.05, 0.45, 0.45, 0.45),
        xlim=(x1, x2), ylim=(y1, y2)
    )
    plot_data(zoomed_ax, df)
    based_ax.indicate_inset_zoom(zoomed_ax, edgecolor="black")
    # Add x-tick labels back in a less obtrusive manner
    xtick_pos = [0.1 * (x + 1) for x in range(10)]
    xtick_labels = [f"{0.1 * (x + 1):.1f}".lstrip('0') for x in range(10)]
    zoomed_ax.set_xticks(xtick_pos, xtick_labels)
    zoomed_ax.tick_params('both', which='major', labelsize=8)
    # Move y-tick labels to the right side to avoid overlapping issues
    zoomed_ax.yaxis.tick_right()


def plot_data(ax, df):
    # Plot the full data first
    ax.scatter(df['Scaling'], df['Runtime'], s=1)

    # Plot the average trendline
    avg_df = df.groupby('Scaling').mean()
    ax.plot(avg_df.index, avg_df['Runtime'])


def get_parser():
    # We only ever need the argument parser when calling this function directly, so import ArgumentParser here
    from argparse import ArgumentParser
    parser = ArgumentParser(
        description="Plot the results of a SCT runtime analysis."
    )

    parser.add_argument(
        '-i', '--input', dest='input_file', type=Path, required=True,
        help="The `.tsv` file containing the results of an SCT runtime analysis "
             "(that is, one of the outputs of `run.py`)."
    )
    parser.add_argument(
        '-o', '--output', dest='output_file', type=Path, required=True,
        help="Where the resulting plot should be placed. "
             "Include the name of the file w/ an extension! (i.e. 'sct_7_xy.svg')"
    )

    parser.add_argument(
        '--title',
        help="The title the plot should have. If not provided, the plot will not have a title."
    )
    parser.add_argument(
        '--zoomed_low_values', action='store_true', dest='zoom',
        help="If present, will add a 'zoomed in' subplot of the lower end values to make them easier to parse."
    )

    return parser


def main(input_file: Path, output_file: Path, title: str, zoom: bool):
    # Confirm the input file exists and is a file
    if not input_file.exists():
        raise ValueError(f"Input file '{input_file}' does not exist!")
    elif not input_file.is_file():
        raise ValueError(f"Input file '{input_file}' was not a file! Perhaps you pointed to a directory by mistake?")

    # Load the data
    df = pd.read_csv(input_file, sep='\t')

    # Plot the results
    plot_results(df, output_file, title, zoom)


if __name__ == '__main__':
    cli_parser = get_parser()
    argvs = cli_parser.parse_args().__dict__
    main(**argvs)
