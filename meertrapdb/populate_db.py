# -*- coding: utf-8 -*-
#
#   2019 Fabian Jankowski
#   Populate the database.
#

from __future__ import print_function
import argparse
from datetime import datetime
from decimal import Decimal
import json
import glob
import logging
import random
from time import sleep
import os.path
import shutil

from astropy.time import Time
from pony.orm import db_session, select
from pytz import timezone

from meertrapdb.config_helpers import get_config
from meertrapdb.db_helpers import setup_db
from meertrapdb.db_logger import DBHandler
from meertrapdb.general_helpers import setup_logging
from meertrapdb.parsing_helpers import parse_spccl_file
from meertrapdb import schema
from meertrapdb.schema import db
from meertrapdb.version import __version__


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
                sb_id_mk=31606,
                sb_id_code_mk="2019-06-21-005",
                proposal_id_mk="DDT-20190513-FC-01",
                proj_main="TRAPUM",
                proj="commissioning",
                utc_start=start,
                sub_array=1,
                observer="Fabian",
                description="TRAPUM Test"
            )

            # observations
            nobs = random.randint(1, 10)
            for _ in range(nobs):
                nbeam = random.randint(1, 390)

                beam_config = schema.BeamConfig(
                    nbeam=nbeam,
                    tiling_mode='fill'
                )

                observation = schema.Observation(
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
                            dm_threshold=5.0,
                            snr_threshold=12.0,
                            width_threshold=500.0,
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
                            observation=observation,
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
    
    Returns
    -------
    plots: list of dict
        Plot files to be copied.
    """

    log = logging.getLogger('meertrapdb')

    config = get_config()
    fsconf = config['filesystem']

    sb_lt_start = datetime.strptime(sb_info['actual_start_time'][:-2],
                                    fsconf["date_formats"]["local"])
    sb_utc_start = sb_lt_start.replace(tzinfo=timezone('UTC'))

    with db_session:
        # schedule blocks
        # check if schedule block is already in the database, otherwise reference it
        sb_id = 5
        sb_queried = schema.ScheduleBlock.select(lambda sb: sb.sb_id == sb_id)[:]

        if len(sb_queried) == 0:
            schedule_block = schema.ScheduleBlock(
                sb_id=sb_id,
                sb_id_mk=sb_info['id'],
                sb_id_code_mk=sb_info['id_code'],
                proposal_id_mk=sb_info['proposal_id'],
                proj_main="TRAPUM",
                proj="DWF run (day 5)",
                utc_start=sb_utc_start,
                sub_array=sb_info['sub_nr'],
                observer=sb_info['owner'],
                description=sb_info['description']
            )

        elif len(sb_queried) == 1:
            log.info("Schedule block is already in the database: {0}".format(sb_id))
            schedule_block = sb_queried[0]

        else:
            msg = 'There are duplicate schedule blocks: {0}'.format(sb_id)
            raise RuntimeError(msg)

        # observations
        # check if observation is already in the database, otherwise reference it
        obs_queried = schema.Observation.select(lambda o: o.utc_start == obs_utc_start)[:]

        if len(obs_queried) == 0:
            beam_config = schema.BeamConfig(
                nbeam=390,
                tiling_mode='fill'
            )

            observation = schema.Observation(
                schedule_block=schedule_block,
                field_name="NGC 6101",
                boresight_ra="16:26:00.00",
                boresight_dec="-73:00:00.0",
                utc_start=obs_utc_start,
                #utc_end=obs_utc_start,
                #tobs=600.0,
                finished=True,
                nant=len(sb_info['antennas_alloc'].split(",")),
                receiver=1,
                cfreq=1284.0,
                bw=856.0,
                nchan=4096,
                npol=1,
                tsamp=0.0003062429906542056,
                beam_config=beam_config
            )

        elif len(obs_queried) == 1:
            log.info("Observation is already in the database: {0}".format(obs_utc_start))
            observation = obs_queried[0]

        else:
            msg = 'There are duplicate observations: {0}'.format(obs_utc_start)
            raise RuntimeError(msg)

        # check if node is already in the database
        # XXX: hardcode node number for now
        node_nr = 1
        node_queried = select(
            n
            for n in schema.Node
            for obs in schema.Observation
            if (obs.utc_start == obs_utc_start
            and n.number == node_nr)
        )[:]

        if len(node_queried) == 0:
            node = schema.Node(
                number=node_nr,
                hostname="tpn-0-{0}".format(node_nr)
            )

        elif len(node_queried) == 1:
            log.info("Node is already in the database: {0}, {1}".format(obs_utc_start, node_nr))
            node = node_queried[0]

        else:
            msg = 'There are duplicate nodes: {0}, {1}'.format(obs_utc_start, node_nr)
            raise RuntimeError(msg)

        # check if pipeline config is already in the database
        pc_queried = select(
            pc
            for pc in schema.PipelineConfig
            for c in pc.sps_candidate
            for obs in c.observation
            for n in c.node
            if (obs.utc_start == obs_utc_start
            and n.number == node_nr)
        )[:]

        if len(pc_queried) == 0:
            pipeline_config = schema.PipelineConfig(
                name="Test",
                version="0.1",
                dd_plan="Test",
                dm_threshold=10.0,
                snr_threshold=10.0,
                width_threshold=500.0,
                zerodm_zapping=True
            )

        elif len(pc_queried) == 1:
            msg = "Pipeline config is already in the database:" + \
                  " {0}, {1}".format(obs_utc_start, node_nr)
            log.info(msg)
            pipeline_config = pc_queried[0]

        else:
            msg = "There are duplicate pipeline configs:" + \
                  " {0}, {1}".format(obs_utc_start, node_nr)
            log.error(msg)
            pipeline_config = pc_queried[0]

        # candidates
        # plot files to be copied
        plots = []

        for item in data:
            cand_mjd = Decimal("{0:.10f}".format(item['mjd']))
            cand_utc = Time(item['mjd'], format='mjd').iso
            cand_beam_nr = int(item['beam'])

            # check if candidate is already in the database
            cand_queried = select(
                (c.mjd, beam.number, obs.utc_start)
                for c in schema.SpsCandidate
                for beam in c.beam
                for obs in c.observation
                if (beam.number == cand_beam_nr
                and obs.utc_start == obs_utc_start
                and abs(c.mjd - cand_mjd) <= Decimal('0.0000000001'))
            )

            if cand_queried.count() > 0:
                msg = "Candidate is already in the database:" + \
                      " {0}, {1}, {2}".format(obs_utc_start, cand_beam_nr, cand_mjd)
                log.error(msg)
                continue

            beam = schema.Beam(
                number=cand_beam_nr,
                coherent=True,
                source="Test source",
                ra=item['ra'],
                dec=item['dec'],
                #gl=0,
                #gb=0
            )

            # assemble candidate plots
            ds_staging = os.path.join(
                fsconf['ingest']['staging_dir'],
                item['plot_file']
            )

            ds_web = ""

            if not os.path.isfile(ds_staging):
                log.warning("Dynamic spectrum plot not found: {0}".format(ds_staging))
            else:
                obs_utc_start_str = obs_utc_start.strftime(fsconf['date_formats']['utc'])
                ds_web = os.path.join(
                    "{0}".format(sb_id),
                    obs_utc_start_str,
                    item['plot_file']
                )

                ds_web_full = os.path.join(
                    fsconf['webserver']['candidate_dir'],
                    ds_web
                )

                ds_processed = os.path.join(
                    fsconf['ingest']['processed_dir'],
                    obs_utc_start_str,
                    item['plot_file']
                )

                file_info = {
                    "staging": ds_staging,
                    "processed": ds_processed,
                    "webserver": ds_web_full
                }

                plots.append(file_info)

            schema.SpsCandidate(
                utc=cand_utc,
                mjd=cand_mjd,
                observation=observation,
                beam=beam,
                snr=item['snr'],
                dm=item['dm'],
                #dm_ex=0.7,
                width=item['width'],
                node=node,
                dynamic_spectrum=ds_web,
                profile="",
                heimdall_plot="",
                pipeline_config=pipeline_config
            )

            # we need to explicitly commit the candidate to the database
            # otherwise the duplicate detection won't work
            db.commit()

    return plots


def copy_plots(plots):
    """
    Copy plots to webserver.

    Parameters
    ----------
    plots: list of dict
        Plot files to be copied.
    
    Raises
    ------
    RuntimeError
        On errors.
    """

    log = logging.getLogger('meertrapdb')

    for item in plots:
        filename = item['staging']
        log.info("Copying plot: {0}".format(filename))

        if not os.path.isfile(filename):
            raise RuntimeError("Staging file does not exist: {0}".format(filename))

        # copy to webserver
        web_dir = os.path.dirname(item['webserver'])

        if not os.path.isdir(web_dir):
            os.makedirs(web_dir)

        shutil.copy(filename, item['webserver'])

        # move to processed
        processed_dir = os.path.dirname(item['processed'])

        if not os.path.isdir(processed_dir):
            os.makedirs(processed_dir)

        shutil.move(filename, item['processed'])


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
    spcll_files = sorted(spcll_files)
    log.info("Found {0} SPCCL files.".format(len(spcll_files)))

    for filename in spcll_files:
        log.info("Processing SPCCL file: {0}".format(filename))

        utc_start_str = os.path.basename(filename)[:19]
        obs_utc_start = datetime.strptime(utc_start_str,
                                          fsconf['date_formats']['utc'])

        log.info("UTC start: {0}".format(obs_utc_start))

        # 3) parse meta data
        spccl_data = parse_spccl_file(filename)

        # check if we have candidates
        if len(spccl_data) > 0:
            log.info("Parsed {0} candidates.".format(len(spccl_data)))
        else:
            log.warning("No candidates found.")
            continue

        # 4) insert data into database
        plots = insert_candidates(spccl_data, sb_info, obs_utc_start)

        # 5) move directory to processed
        if len(plots) > 0:
            log.info("Copying {0} plots.".format(len(plots)))
            copy_plots(plots)
        else:
            log.warning("No plots to copy found.")
        
        # 6) move spccl file to processed
        outfile = os.path.join(
            fsconf['ingest']['processed_dir'],
            utc_start_str,
            os.path.basename(filename)
        )

        outdir = os.path.dirname(outfile)

        if not os.path.isdir(outdir):
            os.makedirs(outdir)

        shutil.move(filename, outfile)

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
