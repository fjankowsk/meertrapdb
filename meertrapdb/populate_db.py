# -*- coding: utf-8 -*-
#
#   2019 Fabian Jankowski
#   Populate the database.
#

from __future__ import print_function
import argparse
from datetime import datetime
import json
import glob
import logging
import random
from time import sleep
import os.path
import shutil

from astropy.time import Time
from pony.orm import db_session
from pytz import timezone

from config_helpers import get_config
from db_helpers import setup_db
from db_logger import  DBHandler
from general_helpers import setup_logging
from parsing_helpers import parse_spccl_file
import schema
from schema import db
from version import __version__


def parse_args():
    parser = argparse.ArgumentParser(
        description="Populate the database."
    )
    
    parser.add_argument(
        'mode',
        choices=['fake', 'init_tables', 'production'],
        help='Mode of operation.'
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=__version__
    )

    return parser.parse_args()


def run_insert_fake_data():
    """
    Insert fake data into the database.
    """

    log = logging.getLogger('meertrapdb')

    start = datetime.now()

    dynamic_spectra = [
        "2019-06-21_00:42:03/beam01/58653.8526978362_DM_9.21_beam_0.jpg",
        "2019-06-21_00:42:03/beam02/58653.8530488991_DM_39.91_beam_0.jpg",
        "tf_plot.jpg"
    ]

    with db_session:
        # schedule blocks
        for _ in range(5):
            schedule_block = schema.ScheduleBlock(
                sb_id=1,
                sb_id_code="2019-06-21-005",
                proposal_id="DDT-20190513-FC-01",
                proj_main="TRAPUM",
                proj="commissioning",
                utc_start=start,
                observer = "Fabian",
                description = "TRAPUM Test"
            )

            # observations
            nobs = random.randint(1, 10)
            for _ in range(nobs):
                nbeam = random.randint(1, 390)

                beam_config = schema.BeamConfig(
                    nbeam=nbeam,
                    tiling_mode='fill'
                )

                obs = schema.Observation(
                    schedule_block=schedule_block,
                    field_name="PKS 1934-638",
                    boresight_ra="08:35:45.124",
                    boresight_dec="-45:35:15",
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
                    beam = schema.Beam(
                            number=beam_nr,
                            coherent=True,
                            source="Test source",
                            ra="08:35:44.7",
                            dec="-45:35:15.7",
                            gl=123.12,
                            gb=-23.1
                    )

                    node_nr = beam_nr // 6
                    node = schema.Node(
                            number=node_nr,
                            hostname="tpn-0-{0}".format(node_nr)
                    )

                    pipeline_config = schema.PipelineConfig(
                            name="Test",
                            version="0.1",
                            dd_plan="Test",
                            dm_threshold="5.0",
                            snr_threshold="12.0",
                            width_threshold="500.0",
                            zerodm_zapping=True
                    )
                    
                    # candidates
                    ncand = random.randint(0, 100)
                    for _ in range(ncand):
                        snr = random.uniform(5, 300)
                        dm = random.uniform(5, 5000)
                        width = random.uniform(1, 500)
                        dynamic_spectrum = random.choice(dynamic_spectra)

                        schema.SpsCandidate(
                            utc=start.isoformat(' '),
                            mjd=58000.123,
                            observation=obs,
                            beam=beam,
                            snr=snr,
                            dm=dm,
                            dm_ex=0.7,
                            width=width,
                            node=node,
                            dynamic_spectrum=dynamic_spectrum,
                            profile="/raid/jankowsk/candidates/test/profile.png",
                            heimdall_plot="/raid/jankowsk/candidates/test/hd.png",
                            pipeline_config=pipeline_config
                        )

    log.info("Done. Time taken: {0}".format(datetime.now() - start))


def insert_candidates(data, sb_info, obs_utc_start):
    """
    Insert candidates into database.

    Parameters
    ----------
    data: numpy.rec
        The parsed candidate data.
    sb_info: dict
        Information about the schedule block.
    obs_utc_start: datetime.datetime
        The start UTC of the observation.
    """

    log = logging.getLogger('meertrapdb')

    config = get_config()
    fsconf = config['filesystem']

    local_time_format = "%Y-%m-%d %H:%M:%S.%f"
    sb_lt_start = datetime.strptime(sb_info['actual_start_time'][:-2],
                                     local_time_format)
    sb_utc_start = sb_lt_start.replace(tzinfo=timezone('UTC'))

    with db_session:
        # schedule blocks
        schedule_block = schema.ScheduleBlock(
            sb_id=4,
            sb_id_code=sb_info['id_code'],
            proposal_id=sb_info['proposal_id'],
            proj_main="TRAPUM",
            proj="DWF run (day 2)",
            utc_start=sb_utc_start,
            observer=sb_info['owner'],
            description=sb_info['description']
            )
        
        beam_config = schema.BeamConfig(
                nbeam=390,
                tiling_mode='fill'
            )

        # observations
        nant = len(sb_info['antennas_alloc'].split(","))

        obs = schema.Observation(
            schedule_block=schedule_block,
            field_name="NGC 6744",
            boresight_ra="08:35:45.124",
            boresight_dec="-45:35:15",
            utc_start=obs_utc_start,
            utc_end=obs_utc_start,
            tobs=600.0,
            finished=True,
            nant=nant,
            receiver=1,
            cfreq=1284.0,
            bw=856.0,
            nchan=4096,
            npol=1,
            tsamp=7.65607476635514e-05,
            beam_config=beam_config
        )
        
        for item in data:
            beam = schema.Beam(
                number=item['beam'],
                coherent=True,
                source="Test source",
                ra=item['ra'],
                dec=item['dec'],
                gl=0,
                gb=0
            )

            node_nr = 0
            node = schema.Node(
                number=node_nr,
                hostname="tpn-0-{0}".format(node_nr)
            )

            pipeline_config = schema.PipelineConfig(
                name="Test",
                version="0.1",
                dd_plan="Test",
                dm_threshold=10.0,
                snr_threshold=10.0,
                width_threshold="500.0",
                zerodm_zapping=True
            )
            
            # candidates
            cand_utc = Time(item['mjd'], format='mjd').iso

            # copy file to webserver directory
            dynamic_spectrum = os.path.join(
                fsconf['ingest']['staging_dir'],
                item['plot_file']
            )

            if os.path.isfile(dynamic_spectrum):
                web_file = os.path.join(
                    fsconf['webserver']['candidate_dir'],
                    item['plot_file']
                )

                shutil.copy(dynamic_spectrum, web_file)
            else:
                log.warning("Dynamic spectrum plot not found: {0}".format(dynamic_spectrum))
                dynamic_spectrum = ""

            schema.SpsCandidate(
                utc=cand_utc,
                mjd=item['mjd'],
                observation=obs,
                beam=beam,
                snr=item['snr'],
                dm=item['dm'],
                dm_ex="",
                width=item['width'],
                node=node,
                dynamic_spectrum=dynamic_spectrum,
                profile="",
                heimdall_plot="",
                pipeline_config=pipeline_config
            )


def get_sb_info():
    """
    Load the schedule block information from file.
    """

    config = get_config()
    fsconf = config['filesystem']

    sb_info_file = os.path.join(
        os.path.dirname(__file__),
        "config",
        fsconf['sb_info_file']
    )

    if not os.path.isfile(sb_info_file):
        raise RuntimeError("SB info file does not exist: {0}".format(sb_info_file))

    with open(sb_info_file, 'r') as fh:
        data = json.load(fh)

    return data


def run_insert_candidates():
    """
    Insert candidates into the database.
    """

    log = logging.getLogger('meertrapdb')
    
    config = get_config()
    fsconf = config['filesystem']

    start = datetime.now()

    # 1) load schedule block information
    sb_info = get_sb_info()

    # 2) check for new directory
    staging_dir = fsconf['ingest']['staging_dir']
    log.info("Staging directory: {0}".format(staging_dir))

    glob_pattern = os.path.join(
        staging_dir,
        "2*_beam??.spccl.log"
    )

    spcll_files = glob.glob(glob_pattern)
    log.info("Found {0} SPCCL files.".format(len(spcll_files)))

    for filename in spcll_files:
        log.info("Processing SPCCL file: {0}".format(filename))

        utc_str = os.path.basename(filename)[:19]
        utc = datetime.strptime(utc_str, fsconf['utc_format'])

        log.info("UTC: {0}".format(utc))

        # 3) parse meta data
        spccl_data = parse_spccl_file(filename)

        # check if we have candidates
        if len(spccl_data) > 0:
            log.info("Parsed {0} candidates.".format(len(spccl_data)))
        else:
            log.warning("No candidates found.")
            continue

        # 4) insert data into database
        insert_candidates(spccl_data, sb_info, utc)

        # 4) move directory to processed
        # processed_dir = os.path.join(
        #     fsconf['ingest']['processed_dir'],
        #     os.path.dirname(utc)
        # )

        # log.info("Processed dir: {0}".format(processed_dir))
        #shutil.move(utc, processed_dir)

    log.info("Done. Time taken: {0}".format(datetime.now() - start))

#
# MAIN
#

def main():
    args = parse_args()

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

    if args.mode == 'fake':
        msg = "This operation mode will populate the database with random" + \
              " fake data. Make sure you want this."
        log.warning(msg)
        sleep(20)
        run_insert_fake_data()
    
    elif args.mode == "init_tables":
        pass
    
    elif args.mode == "production":
        run_insert_candidates()
    
    log.info("All done.")


if __name__ == "__main__":
    main()
