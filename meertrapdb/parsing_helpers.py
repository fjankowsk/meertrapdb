import numpy as np
import os.path


def parse_spccl_file(filename):
    """
    Parse a SPCCL file.
    """

    if not os.path.isfile(filename):
        raise RuntimeError("The SPCCL file does not exist: {0}".format(filename))

    # dtype = [('mjd','float'), ('dm','float'), ('width','float'),
    #          ('snr','float'), ('beam','int'),
    #          ('ra','|S32'), ('dec', '|S32'),
    #          ('fil_file','|S128'), ('plot_file','|S256')]

    names = ['index', 'mjd', 'dm', 'width', 'snr', 'beam', 'ra', 'dec', 'fil_file', 'plot_file']

    data = np.genfromtxt(filename, dtype=None, names=names, delimiter="\t",
                         encoding='ascii',
                         autostrip=True)

    return data


if __name__ == "__main__":
    filename = os.path.join(
        os.path.dirname(__file__),
        'test',
        'used_candidates.spccl.extra'
    )

    data = parse_spccl_file(filename)

    for item in data:
        print(item)
