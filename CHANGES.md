# Version History #

## HEAD ##

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
