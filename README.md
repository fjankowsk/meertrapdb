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

## Sky map data handling ##

The `skymap` code to create, handle, and visualise sky map (e.g. HEALPix) data has been moved into a [separate repository](https://github.com/fjankowsk/skymap/).

## Multi-beam clustering ##

The repository contains a module to cluster (or sift) single-pulse candidates detected in multiple beams, based on their proximity in time and fractional dispersion measure. The parameters of the temporal width of the matching box and the fractional DM threshold can be tweaked as required. Example usage is like this:

```python
from meertrapdb.clustering import Clusterer

clust = Clusterer()
info = clust.match_candidates(candidates)
```

## Usage ##

```bash
$ meertrapdb-benchmark_clusterer
```

```bash
$ meertrapdb-cluster_multibeam -h
usage: meertrapdb-cluster_multibeam [-h] [--dm DM] [--time TIME] [--spccl_version SPCCL_VERSION] filename

Perform multi-beam candidate clustering.

positional arguments:
  filename

optional arguments:
  -h, --help            show this help message and exit
  --dm DM               Fractional DM tolerance. (default: 0.02)
  --time TIME           Time tolerance for matching in milliseconds. (default: 10.0)
  --spccl_version SPCCL_VERSION
                        The version of the input SPCCL file. (default: 2)
```

```bash
$ meertrapdb-make_plots -h
usage: meertrapdb-make_plots [-h] [--version] {heimdall,knownsources,sifting,skymap,timeline,timeonsky}

Make plots from database.

positional arguments:
  {heimdall,knownsources,sifting,skymap,timeline,timeonsky}
                        Mode of operation.

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
```

```bash
$ meertrapdb-parse_datadump -h
usage: meertrapdb-parse_datadump [-h] [--enddate YYYY-MM-DDThh:mm:ss]

Process the sensor data dump.

optional arguments:
  -h, --help            show this help message and exit
  --enddate YYYY-MM-DDThh:mm:ss
                        Process sensor data until this UTC date in ISOT format. (default: None)
```

```bash
$ meertrapdb-populate_db -h
usage: meertrapdb-populate_db [-h] [-s SCHEDULE_BLOCK] [-t] [-v] [--version] {fake,init_tables,known_sources,production,sift,parameters}

Populate the database.

positional arguments:
  {fake,init_tables,known_sources,production,sift,parameters}
                        Mode of operation.

optional arguments:
  -h, --help            show this help message and exit
  -s SCHEDULE_BLOCK, --schedule_block SCHEDULE_BLOCK
                        The schedule block ID to use. (default: None)
  -t, --test_run        Do neither move, nor copy files. This flag works with "production" mode only. (default: False)
  -v, --verbose         Get verbose program output. This switches on the display of debug messages. (default: False)
  --version             show program's version number and exit
```

```bash
$ meertrapdb-search_knownsources
```
