import glob

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


#
# MAIN
#

def main():
    files = glob.glob('fbfuse*.csv')
    files = sorted(files)

    frames = []

    for item in files:
        names = [
            'name',
            'sample_ts',
            'value_ts',
            'value',
            'status'
        ]

        temp = pd.read_csv(
            item,
            names=names,
            na_values='0',
            quotechar='"'
        )

        frames.append(temp)

    df = pd.concat(frames, axis=0)

    # convert to dates
    df['date'] = pd.to_datetime(df['value_ts'], unit='s')

    # add unit field
    df['unit'] = ''

    # convert to mhz
    mask = np.logical_or(
        df['name'] == 'fbfuse_1_fbfmc_array_1_bandwidth',
        df['name'] == 'fbfuse_1_fbfmc_array_1_centre_frequency'
    )
    df.loc[mask, 'value'] = df.loc[mask, 'value'] * 1E-6
    df.loc[mask, 'unit'] = 'MHz'

    # add unit
    mask = (df['name'] == 'fbfuse_1_fbfmc_array_1_coherent_beam_count')
    df.loc[mask, 'unit'] = '#'

    print(df.info())
    print(np.unique(df['name']))

    fig, axs = plt.subplots(
        nrows=len(np.unique(df['name'])),
        ncols=1,
        sharex=True,
        sharey=False
    )

    for i, item in enumerate(np.unique(df['name'])):
        print('Plotting: {0}'.format(item))

        mask = (df['name'] == item)
        sel = df.loc[mask]

        axs[i].scatter(
            sel['date'],
            sel['value'],
            color='C0',
            marker='.',
            s=4,
            label=item,
            zorder=3
        )

        axs[i].grid()
        axs[i].set_ylabel('({0})'.format(sel.at[0, 'unit']))
        axs[i].legend(loc='best', frameon=False)

    axs[-1].set_xlabel('UTC')

    fig.tight_layout()

    fig.savefig(
        'timeline.png',
        dpi=300
    )

    plt.show()

    print('All done.')


if __name__ == "__main__":
    main()
