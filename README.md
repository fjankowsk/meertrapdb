# MeerTRAP Database Backend #

This repository contains the database backend code for the MeerTRAP project at
the MeerKAT telescope.

The code is mainly developed for Python 3 (and in particular version 3.5), but
Python 2 (e.g. version 2.7) should work fine.

For more information feel free to contact: Fabian Jankowski <fabian.jankowski at manchester.ac.uk>

## psrmatch ##

The repository contains a sub-module called psrmatch to efficiently cross-match large numbers of single-pulse candidates with known sources from the ATNF pulsar catalogue or other source catalogues. The cross-matching is based on their detected locations and dispersion measures.

The cross-matcher operates on Astropy SkyCoord objects and input dispersion measures like this:

```python
from psrmatch.matcher import Matcher

m = Matcher()
m.load_catalogue(psrcat)
m.create_search_tree()
m.find_matches(source, dm)
```
