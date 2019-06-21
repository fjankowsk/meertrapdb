# -*- coding: utf-8 -*-
#
#   2019 Fabian Jankowski
#   Populate the database.
#

from __future__ import print_function
import argparse
from datetime import datetime
import logging

from pony.orm import db_session

from config_helpers import get_config
from db_helpers import setup_db
from db_logger import  DBHandler
from general_helpers import setup_logging
import schema
from schema import db
from version import __version__


def parse_args():
    parser = argparse.ArgumentParser(
        description="Populate the database.")
    
    parser.add_argument(
        "--version",
        action="version",
        version=__version__)

    return parser.parse_args()


def insert_fake_data():
    """
    Insert fake data into the database.
    """

    log = logging.getLogger('meertrapdb')

    start = datetime.now()

    for _ in range(100):
        with db_session:
            beam_config = schema.BeamConfig(
                nbeam=400,
                tiling_mode='fill'
            )

            obs = schema.Observation(
                sb_id=1,
                sb_id_code="2019-06-21-005",
                boresight_ra="08:35:45.124",
                boresight_dec="-45:35:15",
                proj_main="TRAPUM",
                proj="commissioning",
                observer="Fabian",
                utc_start=start,
                utc_end=start,
                tobs=600.0,
                finished=True,
                nant=64,
                cfreq=1400.123,
                bw=800.0,
                npol=1,
                tsamp=0.1234,
                beam_config=beam_config
            )

            node = schema.Node(
                hostname="tpn-0-23"
            )

            pipeline_config = schema.PipelineConfig(
                name="",
                version="0.1",
                dd_plan="",
                dm_threshold="5.0",
                snr_threshold="12.0",
                width_threshold="500.0",
                zerodm_zapping=True
            )

            for _ in range(10):
                schema.SpsCandidate(
                    utc=start,
                    mjd=58000.123,
                    observation=obs,
                    beam=123,
                    snr=63.12,
                    dm=89.34,
                    dm_ex=0.01,
                    width=58.9,
                    ra="08:35:44.7",
                    dec="-45:35:15.7",
                    gl=123.12,
                    gb=-23.1,
                    node=node,
                    dynamic_spectrum="/raid/jankowsk/candidates/test/ds.png",
                    profile="/raid/jankowsk/candidates/test/profile.png",
                    heimdall_plot="/raid/jankowsk/candidates/test/hd.png",
                    pipeline_config=pipeline_config
                )

    log.info("Done. Time taken: {0}".format(datetime.now() - start))


#
# MAIN
#

def main():
    parse_args()

    log = logging.getLogger('meertrapdb')
    setup_logging()

    config = get_config()
    dbconf = config['db']

    db.bind(provider=dbconf['provider'],
            host=dbconf['host'],
            port=dbconf['port'],
            user=dbconf['user']['name'],
            passwd=dbconf['user']['password'],
            db=dbconf['database'])

    db.generate_mapping(create_tables=True)

    insert_fake_data()
    
    log.info("All done.")


if __name__ == "__main__":
    main()
