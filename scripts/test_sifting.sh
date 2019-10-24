#!/usr/bin/env bash

for sb in {1..48}
do
	echo "Processing SB: ${sb}"
	time python3 ../meertrapdb/populate_db.py sift -s ${sb}
done
