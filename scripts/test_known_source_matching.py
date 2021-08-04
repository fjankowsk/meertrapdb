import logging
from io import StringIO

from astropy.coordinates import SkyCoord
import astropy.units as units
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import pandas as pd

from meertrapdb.general_helpers import setup_logging
from psrmatch.matcher import Matcher

candidates_str = """ra,dec,dm
14h59m54.01s,-64d27m06.3s,71.22400
14h59m54.01s,-64d27m06.3s,70.91700
14h59m54.01s,-64d27m06.3s,70.61000
14h59m54.01s,-64d27m06.3s,71.53100
14h59m54.01s,-64d27m06.3s,71.83800
14h59m54.01s,-64d27m06.3s,72.14500
"""

df = pd.read_csv(
    StringIO(candidates_str),
    header='infer'
)

print(df.to_string())

pulsar = {
    'ra': '14:53:32.665',
    'dec': '-64:13:16.00',
    'dm': 71.248
}

pcoord = SkyCoord(
    ra=pulsar['ra'],
    dec=pulsar['dec'],
    frame='icrs',
    unit=(units.hourangle, units.deg)
)

m = Matcher(dist_thresh=3.5)
m.load_catalogue('psrcat')
m.create_search_tree()

print('{0:<15} {1:<10} {2:<20}'.format(
    'Separation',
    'DM offset',
    'Matches'
    )
)

for i in range(len(df.index)):
    item = df.loc[i]
    coord = SkyCoord(
        ra=item['ra'],
        dec=item['dec'],
        frame='icrs',
        unit=(units.hourangle, units.deg)
    )

    separation = coord.separation(pcoord).deg

    dm_frac = abs(item['dm'] - pulsar['dm']) / pulsar['dm']

    matches = m.find_matches(coord, item['dm'])
    print('{0:<15.4f} {1:<10.3f} {2:}'.format(separation, dm_frac, matches))

m.plot_catalogue()

ax = plt.gca()

ax.scatter(
    pcoord.ra.deg,
    pcoord.dec.deg,
    s=10,
    color='tab:red',
    marker='*',
    zorder=8
)

ell = Circle(
    xy=(pcoord.ra.deg, pcoord.dec.deg),
    radius=m.dist_thresh,
    facecolor='tab:red',
    edgecolor='tab:red',
    alpha=0.5,
    zorder=3
)

ax.add_artist(ell)


plt.show()
