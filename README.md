# MeerTRAP Database Backend #

This repository contains the database backend code for the [MeerTRAP project](https://www.meertrap.org/) at the MeerKAT telescope. The code is mainly developed for Python 3, but Python 2 from version 2.7 onwards should work fine.

## Author ##

The software is primarily developed and maintained by Fabian Jankowski. For more information feel free to contact me via: fabian.jankowski at manchester.ac.uk.

## Citation ##

If you make use of the software, please add a link to this repository and cite our upcoming paper. See the CITATION file.

## Installation ##

The easiest and recommended way to install the software is through `pip` directly from the bitbucket repository. For example, to install the master branch of the code, use the following command:

`pip3 install git+https://bitbucket.org/jankowsk/meertrapdb.git@master`

## Known source matching ##

The `psrmatch` known source matching code has been moved into a [separate repository](https://bitbucket.org/jankowsk/psrmatch/).

## Multi-beam clustering ##

The repository contains a module to cluster (or sift) single-pulse candidates detected in multiple beams, based on their proximity in time and fractional dispersion measure. The parameters of the temporal width of the matching box and the fractional DM threshold can be tweaked as required. Example usage is like this:

```python
from meertrapdb.clustering import Clusterer

clust = Clusterer()
info = clust.match_candidates(candidates)
```
