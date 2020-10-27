# Version History #

## HEAD ##

* Add representation and string functions to the matcher and the clusterer.
* Simplified importing the known-source matcher and the multibeam clusterer.
* Improved and corrected the python setup file. Both `meertrapdb` and `psrmatch` are now correctly included in the package list, and the package data (configuration files and catalogue data) are now included properly too.

## 0.7 (2020-10-27) ##

* Bumped `meertrapdb` to version 0.7. `psrmatch` stays at version 0.3.
* Added section about installing the software to the readme file.
* Added `tiling_epoch`, `ref_freq` and `target` fields to the database schema and added code to populate them.
* Copy or move the SPCCL and summary files into the corresponding node directories in the processed directory, replicating the ingest directory hierarchy.
* Populated the `finished`, `tobs` and `receiver` fields in the database.
* Treated special case when `utc_stop` is not present in the run summary file.
* Added code to copy the run summary files to the processed directory to retain a full history of what was ingested.
* Increased the length of project fields in the database schema.
* Major changes to the candidate ingestion code. Populate meta data from run summary files and allow different parameters per Observation. Added more fields to the database and added new Tiling table. The Tiling table will allow us to store multiple tilings per pointing, which will become useful soon. In particular, we correctly populate the following fields now: `sb_utc_start, obs_utc_start, sb_id_mk, sb_id_code, proposal_id_mk, proj_main, sub_array, observer, description, cb_angle, cb_x, cb_y, nbeam, overlap, utc_end, cb_nant, ib_nant, cfreq, bw, nchan, tsamp, (pipeline) name, version, dd_plan, dm_threshold, snr_threshold, width_threshold`.
* Added functionality to read meta data from the new JSON run summary files that are output by the control system. We call them summary file version 2.
* Moved schedule block parsing code into own module. Added regression tests for it.
* Require user input before ingesting data into an existing schedule block and before running in 'fake' operation mode. This should prevent us better from damaging the database content involuntarily.

## 0.6.2 (2020-10-22) ##

* Bumped `psrmatch` to version 0.3 and `meertrapdb` to version 0.6.2.
* Code formatting improvements and refactoring to increase code readability.
* Removed legacy python 2 compatibility code.
* `psrmatch`: Added initial code to allow for the handling of multiple catalogues at a time. Added simple functions to load, unload and check the status of the matcher, and corresponding regression tests.
* `psrmatch`: Added regression test using known-good results from fake source data.
* `psrmatch`: Switched to the latest version of the ATNF pulsar catalogue (version 1.64 beta).
* Added script to benchmark the multi-beam clustering algorithm and to determine its time complexity. The benchmark script outputs a runtime plot for visual inspection. On my laptop, the `Clusterer` operates in sub-quadratic time with increasing number of input candidates n as T(n) = O(n^1.6).
* Adjusted the code throughout to use the new multi-beam `Clusterer` module and documented it. Removed old clustering code.
* Moved the multi-beam clustering code into a new `Clusterer` class to allow for easier code reuse. The code is functionally identical, as verified using regression tests.
* Added regression tests using `nose2` and the corresponding infrastructure. Implemented tests for the SPCCL parsing helpers and the multi-beam clusterer.
* `psrmatch`: Now that we use a distance threshold early in the spatial lookup, we can save some time later in the processing chain. This change resulted in a speedup of a factor of about 12 in my test setup on my laptop. My laptop manages to do about 800 lookups per second now.
* `psrmatch`: Added script to test and benchmark the known source matcher on random input.
* `psrmatch`: Bumped the nearest neighbor tree lookup from 5 to the 25 nearest sources and made it a parameter. The spatial density of pulsars is high in the Galactic plane, given MeerKAT's sensitivity.
* Added the `healpy` python module for Healpix tesselation of the surveyed sky and added a simple test script.

## 0.6 (2020-07-09) ##

* Bump `meertrapdb` to version 0.6 and `psrmatch` to version 0.2.
* `psrmatch`: Keep track of the supported catalogues and allow the user to query them.
* `psrmatch`: Wrap catalogue data loading in the `matcher` class and hide away that code from the user. Catalogues can now be loaded by name.
* Upgraded to version 1.63 of the ATNF pulsar catalogue in `psrmatch`.
* Code formatting improvements to increase readability.
* Add Milky Way contribution to dispersion measure. Determine the mean Galactic DM based on the results from the `NE2001` and `YMW16` models.
* Populate Galactic coordinates after candidate ingest in the `parameters` step.
* Add fields for Milky Way DM and MTC and Fetch plots.
* Switched to SPCCL version 2 candidate files by default.
* Added Slack notification implemented by Mat Malenta. A short summary gets sent to a certain Slack channel upon successful ingest of candidates.
* Implemented parsing of SPCCL version 2 candidate files. These have the beam mode (coherent or incoherent) specified.
* Added the total sky area covered by the surveys to the output.
* Match Galactic latitude bins with the SUPERB limits.
* Bin the survey pointing data in Galactic latitude.
* Compute the total unique area covered by the survey pointings based on filled polygons/hexagons.
* Added functionality to produce various plots of the survey pointings so far, both in equatorial and Galactic coordinates.

## 0.5 (2020-01-29) ##

This version of the software was extensively tested over the last three months and in particular using the candidates from the extensive runs over the Christmas/New Year holiday break.

* In the multi-beam clustering code, check if a candidate was already assigned to a cluster. Do not process it if that is the case. This speeds up the clustering and, more importantly, should avoid singular candidates at the cluster ends in MJD. The previous implementation was treating cluster members at the trailing edge of the cluster incorrectly.
* Convert `psrmatch` into a separate class and module, so that it can be used in other code. Use separate versioning for it (version 0.1).
* Added `psrmatch`, a simple known-source matching algorithm in spatial - DM space based on a k-d search tree for performance. It uses the ATNF pulsar catalogue for now. The code identifies candidates from known pulsars based on thresholding in both dimensions.
* Added simplistic code to find periodic sources in the DM - time plane using heuristical (statistical) methods. This was later backed out again, in favour of a simpler threshold-based spatial matching code.

## 0.4 (2019-10-25) ##

* Added heimdall-like plot of candidate dispersion measures versus time, including S/N and width.
* Complete rewrite of the multi-beam clustering (`sift`) logic that is now based on numpy array masking operations.
* Added option to make plot to evaluate the multibeam sifting performance.
* Added option to make plot of S/N timeline by schedule block ID and in total.
* Added `make_plots` script to generate statistics plots from the database.
* Added check to `sift` mode to test whether the requested schedule block is present in the database.
* Added check to `production` mode that tests whether the requested schedule block is already in the database. This should prevent the user from ingesting candidates from multiple runs into the same schedule block.
* The schedule block ID is now specified as a commandline option, rather than in the configuration file, to simplify the ingestion process for the user.
* The results from the multi-beam sifting operation are written into a separate database table. Subsequent sifting runs overwrite the previous results without modifying the candidate data. This allows one to trial different sifting parameters.
* Added multi-beam clustering (`sift`) code and hooked it up to the database. It is run as part of the ingestion process, but can be invoked separately. A stand-alone script is available as well that works on SPCCL file input.

## 0.3 (2019-09-04) ##

This version of the code has seen constant use and testing over the last two months.

* The candidates are now grouped by absolute beam number.
* Added `test_run` command line option that is useful for testing the database ingest logic. It is only valid for `production` mode. Files are neither copied, nor moved when the option is specified.
* Moved schedule block ID definition into the configuration file
* We switched to a much improved directory structure for storing the candidate files on disk. The code was adjusted to reflect that. As a consequence, we now know the nodes on which the candidates were generated.
* Added contributors file and extended description in the readme file
* Added normal user to the docker image to run the ingest script
* Sorted imports
* General code cleanup
* Switched to Python 3

## 0.2 (2019-07-01) ##

This version reflects the state of the code after the DWF run.

* Increase precision to 10 decimal digits for the MJD field, convert other fields to unique
* Reference schedule blocks and observations if they are already in the database
* Added logic to prevent adding duplicate candidates
* Parse schedule block information from JSON dump
* Added script to get schedule block information, imported from `KATPortalClient`
* Copy candidate plots to webserver
* Parse SPCCL files
* Added function to populate database with real candidates
* Added ScheduleBlock entity above Observation in database schema
* Added function to populate database with fake data
* Work around limitations of MariaDB 5.5 for the current run, switch to using bare metal database
* Use `Decimal` data type properly for database fields

## 0.1 (untagged) ##

* Initial configuration file for catalogue lookup
* Packaged the code as a python package
* Added simple code to analyse benchmark results
* Added YAML configuration file
* Added simple database benchmark code
* Implemented database table schema using `ponyorm`
* Added script to automatically set up users, database and tables
* Use of `ponyorm` object relational mapper and `mysql` python wrapper
* Docker file for MariaDB database tests
