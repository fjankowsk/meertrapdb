# MeerTRAP Database Backend #

This repository contains the database backend code for the MeerTRAP project at the MeerKAT telescope. The code is mainly developed for Python 3 (and in particular version 3.7), but Python 2 (e.g. version 2.7) should work fine.

## Author ##

The software is primarily developed and maintained by Fabian Jankowski. For more information feel free to contact me via: fabian.jankowski at manchester.ac.uk.

## Citation ##

If you make use of the software, please add a link to this repository and cite our upcoming paper. See the CITATION file.

## Installation ##

The easiest and recommended way to install the software is through `pip` directly from the bitbucket repository. For example, to install the master branch of the code, use the following command:

`pip3 install git+https://bitbucket.org/jankowsk/meertrapdb.git@master`

## Known source matching ##

The repository contains a sub-module called `psrmatch` to efficiently cross-match large numbers of single-pulse candidates with known sources from the ATNF pulsar catalogue or other source catalogues. The cross-matching is based on their detected locations and dispersion measures.

The cross-matcher operates on Astropy SkyCoord objects and input dispersion measures like this:

```python
from psrmatch import Matcher

m = Matcher()
m.load_catalogue('psrcat')
m.create_search_tree()
m.find_matches(source, dm)
```

The list of supported catalogues can be queried using the `m.get_supported_catalogues()` function that returns a list of catalogue names.

## Multi-beam clustering ##

The repository contains a module to cluster (or sift) single-pulse candidates detected in multiple beams, based on their proximity in time and fractional dispersion measure. The parameters of the temporal width of the matching box and the fractional DM threshold can be tweaked as required. Example usage is like this:

```python
from meertrapdb.clustering import Clusterer

clust = Clusterer()
info = clust.match_candidates(candidates)
```
