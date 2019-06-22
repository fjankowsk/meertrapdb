# -*- coding: utf-8 -*-
#
#   2019 Fabian Jankowski
#   Populate the database.
#

from __future__ import print_function
import argparse
from datetime import datetime
import logging
import random

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

    with db_session:
        # observations
        for _ in range(1000):
            nbeam = random.randint(1, 390)

            beam_config = schema.BeamConfig(
                nbeam=nbeam,
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
                receiver=1,
                cfreq=1284.0,
                bw=856.0,
                nchan=4096,
                npol=1,
                tsamp=7.65607476635514e-05,
                beam_config=beam_config
            )

            # beams
            for beam_nr in range(nbeam):
                node_nr = beam_nr // 6

                node = schema.Node(
                        number=node_nr,
                        hostname="tpn-0-{0}".format(node_nr)
                    )
                
                # candidates
                ncand = random.randint(0, 100)
                for _ in range(ncand):
                    snr = random.uniform(5, 300)
                    dm = random.uniform(5, 5000)
                    width = random.uniform(1, 500)

                    pipeline_config = schema.PipelineConfig(
                        name="Test",
                        version="0.1",
                        dd_plan="Test",
                        dm_threshold="5.0",
                        snr_threshold="12.0",
                        width_threshold="500.0",
                        zerodm_zapping=True
                    )

                    beam = schema.Beam(
                        number=beam_nr,
                        coherent=True,
                        source="Test source",
                        ra="08:35:44.7",
                        dec="-45:35:15.7",
                        gl=123.12,
                        gb=-23.1
                    )

                    schema.SpsCandidate(
                        utc=start,
                        mjd=58000.123,
                        observation=obs,
                        beam=beam,
                        snr=snr,
                        dm=dm,
                        dm_ex=0.7,
                        width=width,
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
