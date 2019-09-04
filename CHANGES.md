# Version History #

## HEAD ##

## 0.3 (2019-09-04) ##

This version of the code has seen constant use and testing over the last two months.

* The candidates are now grouped by absolute beam number
* Added `test_run` command line option that is useful for testing the database ingest logic. It is only valid for `production` mode. Files are neither copied, nor moved when the option is specified.
* Moved schedule block ID definition into the configuration file
* We switched to a much improved directory structure for storing the candidate files on disk. The code was adjusted to reflect that. As a consequence, we now know the nodes on which the candidates were generated.
* The node numbers are included now for each candidate
* Switched to more descriptive directory structure for storing candidate files
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
