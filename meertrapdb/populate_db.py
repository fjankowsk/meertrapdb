# -*- coding: utf-8 -*-
#
#   2019 - 2020 Fabian Jankowski
#   Populate the database.
#

from __future__ import print_function
import argparse
from datetime import datetime
from decimal import Decimal
import glob
import json
import logging
import os.path
import random
import requests as req
import shutil
import sys
import time
from time import sleep

from astropy.coordinates import SkyCoord
from astropy.time import Time
import astropy.units as u
import numpy as np
from numpy.lib import recfunctions
from pony.orm import (db_session, delete, select)
from pytz import timezone

from meertrapdb.config_helpers import get_config
from meertrapdb.db_helpers import setup_db
from meertrapdb.db_logger import DBHandler
from meertrapdb.general_helpers import setup_logging
from meertrapdb.multibeam_sifter import match_candidates
from meertrapdb.parsing_helpers import parse_spccl_file
from meertrapdb import schema
from meertrapdb.schema import db
from meertrapdb.version import __version__
from psrmatch.catalogue_helpers import parse_psrcat
from psrmatch.matcher import Matcher

# astropy generates members dynamically, pylint therefore fails
# disable the corresponding pylint test for now
# pylint: disable=E1101


def parse_args():
    parser = argparse.ArgumentParser(
        description="Populate the database."
    )

    parser.add_argument(
        'mode',
        choices=[
            'fake', 'init_tables', 'known_sources', 'production', 'sift',
            'parameters'
            ],
        help='Mode of operation.'
    )

    parser.add_argument(
        '-s', '--schedule_block',
        dest='schedule_block',
        type=int,
        help='The schedule block ID to use.'
    )

    parser.add_argument(
        '-t', '--test_run',
        action='store_true',
        help='Do neither move, nor copy files. This flag works with "production" mode only.'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Get verbose program output. This switches on the display of debug messages.'
    )

    parser.add_argument(
        "--version",
        action="version",
        version=__version__
    )

    return parser.parse_args()


def check_if_schedule_block_exists(schedule_block):
    """
    Check if schedule block is already in the database.

    Parameters
    ----------
    schedule_block: int
        The schedule block ID of candidates in the database.

    Raises
    ------
    RuntimeError
        In case of duplicate schedule blocks.
    """

    with db_session:
        sb_queried = schema.ScheduleBlock.select(lambda sb: sb.sb_id == schedule_block)[:]

        if len(sb_queried) == 1:
            pass

        elif len(sb_queried) > 1:
            msg = 'There are duplicate schedule blocks: {0}'.format(schedule_block)
            raise RuntimeError(msg)

        else:
            print('The schedule block is not in the database: {0}'.format(schedule_block))
            sys.exit(1)


def run_fake():
    """
    Run the processing for 'fake' mode, i.e. insert fake data into the database.
    """

    log = logging.getLogger('meertrapdb.populate_db')

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


def insert_candidates(data, sb_id, sb_info, obs_utc_start, node_name):
    """
    Insert candidates into database.

    Parameters
    ----------
    data: numpy.rec
        The parsed candidate data.
    sb_id: int
        The ID of the schedule block in the MeerTRAP database.
    sb_info: dict
        Information about the schedule block.
    obs_utc_start: datetime.datetime
        The start UTC of the observation.
    node_name: str
        The name of the node, e.g. `tpn-0-37`.
    
    Returns
    -------
    plots: list of dict
        Plot files to be copied.
    """

    log = logging.getLogger('meertrapdb.populate_db')

    config = get_config()
    fsconf = config['filesystem']

    sb_lt_start = datetime.strptime(sb_info['actual_start_time'][:-2],
                                    fsconf["date_formats"]["local"])
    sb_utc_start = sb_lt_start.replace(tzinfo=timezone('UTC'))

    with db_session:
        # 1) schedule blocks
        # check if schedule block is already in the database, otherwise reference it
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

        # 2) observations
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

        # 3) nodes
        # check if node is already in the database, otherwise reference it
        node_nr = int(node_name[6:])
        log.info("Node number: {0}".format(node_nr))

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

        # 4) pipeline config
        # check if pipeline config is already in the database, otherwise reference it
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
        
        # 5) beams
        # check if beam is already in the database, otherwise reference it

        # this assumes that there is one candidate file per beam, i.e no
        # mixing of beams within a candidate file
        beam_nr = int(data['beam'][0])
        beam_coherent = bool(data['coherent'][0])
        beam_source = "Test source"
        ra = data['ra'][0]
        dec = data['dec'][0]

        beam_queried = select(
            beam
            for beam in schema.Beam
            for c in beam.sps_candidate
            for obs in c.observation
            for n in c.node
            if (obs.utc_start == obs_utc_start
            and beam.number == beam_nr
            and n.number == node_nr
            and beam.coherent == beam_coherent)
        )[:]

        if len(beam_queried) == 0:
            beam = schema.Beam(
                number=beam_nr,
                coherent=beam_coherent,
                source=beam_source,
                ra=ra,
                dec=dec
            )

        elif len(beam_queried) == 1:
            msg = "Beam is already in the database:" + \
                  " {0}, {1}, {2}".format(obs_utc_start, node_nr, beam_nr)
            log.info(msg)
            beam = beam_queried[0]

        else:
            msg = "There are duplicate beams:" + \
                  " {0}, {1}, {2}".format(obs_utc_start, node_nr, beam_nr)
            log.error(msg)
            beam = beam_queried[0]

        # 6) candidates
        # plot files to be copied
        plots = []

        for item in data:
            cand_mjd = Decimal("{0:.10f}".format(item['mjd']))
            cand_utc = Time(item['mjd'], format='mjd').iso

            # check if candidate is already in the database
            cand_queried = select(
                (c.mjd, beam.number, obs.utc_start)
                for c in schema.SpsCandidate
                for beam in c.beam
                for obs in c.observation
                if (beam.number == beam_nr
                and beam.coherent == beam_coherent
                and obs.utc_start == obs_utc_start
                and abs(c.mjd - cand_mjd) <= Decimal('0.0000000001'))
            )

            if cand_queried.count() > 0:
                msg = "Candidate is already in the database:" + \
                      " {0}, {1}, {2}".format(obs_utc_start, beam_nr, cand_mjd)
                log.error(msg)
                continue

            # assemble candidate plots
            obs_utc_start_str = obs_utc_start.strftime(fsconf['date_formats']['utc'])

            ds_staging = os.path.join(
                fsconf['ingest']['staging_dir'],
                obs_utc_start_str,
                node_name,
                item['plot_file']
            )

            ds_web = ""

            if not os.path.isfile(ds_staging):
                log.warning("Dynamic spectrum plot not found: {0}".format(ds_staging))
            else:
                ds_web = os.path.join(
                    "{0}".format(sb_id),
                    obs_utc_start_str,
                    node_name,
                    item['plot_file']
                )

                ds_web_full = os.path.join(
                    fsconf['webserver']['candidate_dir'],
                    ds_web
                )

                ds_processed = os.path.join(
                    fsconf['ingest']['processed_dir'],
                    obs_utc_start_str,
                    node_name,
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

    log = logging.getLogger('meertrapdb.populate_db')

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


def run_production(schedule_block, test_run):
    """
    Run the processing for 'production' mode, i.e. insert real candidates into the database.

    Parameters
    ----------
    schedule_block: int
        The schedule block ID to use to reference the candidates in the database.
    test_run: bool
        Determines whether to run in test mode, where no files are moved, nor copied.

    Returns
    -------
    start_time: str
        The start time of the schedule block.
    """

    log = logging.getLogger('meertrapdb.populate_db')
    
    config = get_config()
    fsconf = config['filesystem']

    start = datetime.now()

    # check if schedule block is already in the database
    with db_session:
        sb_queried = schema.ScheduleBlock.select(lambda sb: sb.sb_id == schedule_block)[:]

        if len(sb_queried) == 1:
            msg = 'The schedule block is already in the database: {0}\n'.format(schedule_block) + \
                  'Are you sure you want to continue?'
            log.warning(msg)
            sleep(20)

        elif len(sb_queried) > 1:
            msg = 'There are duplicate schedule blocks: {0}'.format(schedule_block)
            raise RuntimeError(msg)

    # 1) load schedule block information
    sb_info = get_sb_info()
    start_time = sb_info['actual_start_time'][:-2]

    # 2) check for new directory
    staging_dir = fsconf['ingest']['staging_dir']
    log.info("Staging directory: {0}".format(staging_dir))

    glob_pattern = os.path.join(
        staging_dir,
        fsconf['ingest']['glob_pattern']
    )
    log.info("Glob pattern: {0}".format(glob_pattern))

    spcll_files = glob.glob(glob_pattern)
    spcll_files = sorted(spcll_files)
    log.info("Found {0} SPCCL files.".format(len(spcll_files)))

    for filename in spcll_files:
        log.info("Processing SPCCL file: {0}".format(filename))

        utc_start_str = os.path.basename(filename)[:19]
        obs_utc_start = datetime.strptime(utc_start_str,
                                          fsconf['date_formats']['utc'])

        log.info("UTC start: {0}".format(obs_utc_start))

        node_name = os.path.basename(
            os.path.dirname(filename)
        )

        log.info("Node: {0}".format(node_name))

        # 3) parse candidate data
        spccl_data = parse_spccl_file(filename, config['candidates']['version'])

        # check if we have candidates
        if len(spccl_data) > 0:
            log.info("Parsed {0} candidates.".format(len(spccl_data)))
        else:
            log.warning("No candidates found.")
            continue

        # 4) insert data into database
        plots = insert_candidates(spccl_data, schedule_block, sb_info, obs_utc_start, node_name)

        if not test_run:
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

    return start_time


def run_sift(schedule_block):
    """
    Run the processing for 'sift' mode.

    Parameters
    ----------
    schedule_block: int
        The schedule block ID to process.

    Returns
    -------
    ncands: int
        The total number of candidates loaded.
    """

    log = logging.getLogger('meertrapdb.populate_db')

    config = get_config()
    sconfig = config['sifter']

    start = datetime.now()

    # check if schedule block is in the database
    check_if_schedule_block_exists(schedule_block)

    # delete any previous sift results for that schedule block
    log.info('Deleting previous sift results for schedule block: {0}'.format(schedule_block))
    with db_session:
        delete(
            sr
            for sr in schema.SiftResult
            for c in sr.sps_candidate
            for obs in c.observation
            for sb in obs.schedule_block
            if (sb.sb_id == schedule_block)
        )

    # get the candidates
    log.info('Loading candidates from database.')
    with db_session:
        candidates = select(
                    (c.id, c.mjd, c.dm, c.snr, beam.number)
                    for c in schema.SpsCandidate
                    for beam in c.beam
                    for obs in c.observation
                    for sb in obs.schedule_block
                    if (sb.sb_id == schedule_block)
                ).sort_by(1)[:]

    if len(candidates) == 0:
        raise RuntimeError('No single-pulse candidates found.')

    log.info('Candidates loaded: {0}'.format(len(candidates)))

    # convert to numpy record
    candidates = [item for item in candidates]
    dtype = [('index',int), ('mjd',float), ('dm',float), ('snr',float), ('beam',int)]
    candidates = np.array(candidates, dtype=dtype)

    info = match_candidates(candidates, sconfig['time_thresh'], sconfig['dm_thresh'])

    # write results back to database
    log.info('Writing results into database.')
    with db_session:
        for item in info:
            # find sps candidate
            cand_queried = schema.SpsCandidate.select(lambda c: c.id == int(item['index']))[:]

            if len(cand_queried) == 1:
                cand = cand_queried[0]
            else:
                raise RuntimeError('Something is wrong with the candidate index mapping: {0}, {1}, {2}'.format(
                                   item['index'], len(cand_queried), cand_queried))

            # find cluster head
            head_queried = schema.SpsCandidate.select(lambda c: c.id == int(item['head']))[:]

            if len(head_queried) == 1:
                head = head_queried[0]
            else:
                raise RuntimeError('Something is wrong with the head index mapping: {0}, {1}, {2}'.format(item['head'],
                                   len(head_queried), head_queried))
            
            schema.SiftResult(
                sps_candidate=cand,
                cluster_id=item['cluster_id'],
                head=head,
                is_head=item['is_head'],
                members=item['members'],
                beams=item['beams']
            )

    log.info("Done. Time taken: {0}".format(datetime.now() - start))

    return len(candidates)


def run_known_sources(schedule_block):
    """
    Run the processing for 'known_sources' mode.

    Parameters
    ----------
    schedule_block: int
        The schedule block ID to process.

    Returns
    -------
    nheads: int
        The number of cluster heads loaded.
    nmatched: int
        The number of cluster heads that have known matching sources.
    """

    log = logging.getLogger('meertrapdb.populate_db')

    config = get_config()
    ksconfig = config['knownsources']

    start = datetime.now()

    # check if schedule block is in the database
    check_if_schedule_block_exists(schedule_block)

    # delete any previous known source matching for that schedule block
    log.info('Deleting previous known source matching for schedule block: {0}'.format(schedule_block))
    with db_session:
        # just remove the links to the known source entries
        candidates = select(
                    c
                    for c in schema.SpsCandidate
                    for obs in c.observation
                    for sr in c.sift_result
                    for sb in obs.schedule_block
                    if (sb.sb_id == schedule_block
                        and sr.is_head)
                )[:]

        for cand in candidates:
            cand.known_source.clear()

    # prepare known source matcher
    m = Matcher(dist_thresh=ksconfig['dist_thresh'], dm_thresh=ksconfig['dm_thresh'])

    log.info('Loading pulsar catalogue.')

    psrcat = parse_psrcat(
        os.path.join(
            os.path.dirname(__file__),
            '..',
            'psrmatch',
            'catalogues',
            'psrcat_v161.txt'
        )
    )

    m.load_catalogue(psrcat)

    log.info('Creating k-d search tree.')
    m.create_search_tree()

    # get the cluster heads
    log.info('Loading cluster heads from database.')
    with db_session:
        candidates = select(
                    (c.id, c.dm, beam.ra, beam.dec)
                    for c in schema.SpsCandidate
                    for beam in c.beam
                    for obs in c.observation
                    for sr in c.sift_result
                    for sb in obs.schedule_block
                    if (sb.sb_id == schedule_block
                        and sr.is_head)
                ).sort_by(1)[:]

    if len(candidates) == 0:
        raise RuntimeError('No cluster heads found.')

    log.info('Cluster heads loaded: {0}'.format(len(candidates)))

    # convert to numpy record
    candidates = [item for item in candidates]
    dtype = [
        ('index',int), ('dm',float), ('ra','|U32'), ('dec','|U32')
    ]
    candidates = np.array(candidates, dtype=dtype)

    coords = SkyCoord(ra=candidates['ra'],
                      dec=candidates['dec'],
                      frame='icrs',
                      unit=(u.hourangle, u.deg))

    dtype = [
        ('index',int), ('has_match',bool), ('source','|U32'), ('catalogue','|U32'),
        ('dm',float), ('type','|U32')
    ]
    info = np.zeros(len(candidates), dtype=dtype)

    for i in range(len(candidates)):
        cand = candidates[i]

        match = m.find_matches(coords[i], cand['dm'])

        info['index'][i] = cand['index']

        if match is None:
            info['has_match'][i] = False
        else:
            info['has_match'][i] = True
            info['source'][i] = match['psrj']

            for field in ['catalogue', 'dm', 'type']:
                info[field][i] = match[field]

    # consider only those cluster heads that have a match
    matched = info[info['has_match'] == True]

    # write results back to database
    log.info('Writing results into database.')
    with db_session:
        for item in matched:
            # find sps candidate
            cand_queried = schema.SpsCandidate.select(lambda c: c.id == int(item['index']))[:]

            if len(cand_queried) == 1:
                cand = cand_queried[0]
            else:
                raise RuntimeError('Something is wrong with the candidate index mapping: {0}, {1}, {2}'.format(
                                   item['index'], len(cand_queried), cand_queried))

            # find known source
            ks_queried = schema.KnownSource.select(lambda c: c.name == item['source'])[:]

            if len(ks_queried) == 0:
                # insert known source and link
                schema.KnownSource(
                    sps_candidate=cand,
                    name=item['source'],
                    catalogue=item['catalogue'],
                    dm=item['dm'],
                    source_type=item['type']
                )

                db.commit()

            elif len(ks_queried) == 1:
                # link sps candidate and known source
                ks = ks_queried[0]
                cand.known_source.add(ks)

            else:
                raise RuntimeError('Duplicate known source names are present: {0}, {1}, {2}'.format(
                                   item['source'], len(ks_queried), ks_queried))

    log.info("Done. Time taken: {0}".format(datetime.now() - start))

    return len(candidates), len(matched)


def send_notification(info):
    """
    Send notification to Slack.

    Parameters
    ----------
    info: dict
        All parameters for the Slack message.
    """

    log = logging.getLogger('meertrapdb.populate_db')
    config = get_config()
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

    text = 'SB: {0}, start date: {1}, raw candidates: {2}, unique heads: {3}, unmatched unique heads: {4}'.format(
        info['schedule_block'],
        info['start_time'],
        info['raw_cands'],
        info['unique_heads'],
        info['unique_heads'] - info['known_matched']
    )

    message = {
        'pretext': '* {0} NEW SB injected:* \n'.format(current_time),
        'color': config['notifier']['colour'],
        'text': text
    }

    cand_message = {
        'attachments': [message]
    }
    message_json = json.dumps(cand_message)

    try:
        req.post(config['notifier']['http_link'], data=message_json, timeout=2)
    except Exception:
        log.error('Something happened when trying to send the data to Slack.')
        log.error(sys.exc_info()[0])


def run_parameters(schedule_block):
    """
    Run the processing for 'parameters' mode.

    Parameters
    ----------
    schedule_block: int
        The schedule block ID to process.
    """

    log = logging.getLogger('meertrapdb.populate_db')

    start = datetime.now()

    # check if schedule block is in the database
    check_if_schedule_block_exists(schedule_block)

    # get the beams
    log.info('Loading beams from database.')
    with db_session:
        beams = select(
                    (beam.id, beam.number, beam.coherent, beam.ra, beam.dec)
                    for beam in schema.Beam
                    for c in beam.sps_candidate
                    for obs in c.observation
                    for sb in obs.schedule_block
                    if (sb.sb_id == schedule_block)
                ).sort_by(1)[:]

    if len(beams) == 0:
        raise RuntimeError('No beams found.')

    log.info('Beams loaded: {0}'.format(len(beams)))

    # convert to numpy record
    beams = [item for item in beams]
    dtype = [
        ('id',int), ('number',int), ('coherent',bool), ('ra','|U32'), ('dec','|U32')
    ]
    beams = np.array(beams, dtype=dtype)

    coords = SkyCoord(
        ra=beams['ra'],
        dec=beams['dec'],
        frame='icrs',
        unit=(u.hourangle, u.deg)
    )

    beams = recfunctions.append_fields(beams, 'gl', coords.galactic.l)
    beams = recfunctions.append_fields(beams, 'gb', coords.galactic.b)

    for item in beams:
        print(item)

    log.info("Done. Time taken: {0}".format(datetime.now() - start))


#
# MAIN
#

def main():
    args = parse_args()

    # sanity check test_run flag
    if args.test_run is True \
    and args.mode != 'production':
        sys.exit('The "test_run" flag is only valid for "production" mode.')

    log = logging.getLogger('meertrapdb.populate_db')

    if args.verbose:
        setup_logging(logging.DEBUG)
    else:
        setup_logging(logging.INFO)

    config = get_config()
    dbconf = config['db']

    db.bind(
        provider=dbconf['provider'],
        host=dbconf['host'],
        port=dbconf['port'],
        user=dbconf['user']['name'],
        passwd=dbconf['user']['password'],
        db=dbconf['database']
    )

    db.generate_mapping(create_tables=True)

    # check that there is a schedule block id given
    if args.mode in ['known_sources', 'production', 'sift', 'parameters']:
        if not args.schedule_block:
            print('Please specify a schedule block ID to use.')
            sys.exit(1)

    if args.mode == 'fake':
        msg = "This operation mode will populate the database with random" + \
              " fake data. Make sure you want this."
        log.warning(msg)
        sleep(20)
        run_fake()

    elif args.mode == "init_tables":
        pass

    elif args.mode == "known_sources":
        run_known_sources(args.schedule_block)

    elif args.mode == "production":
        start_time = run_production(args.schedule_block, args.test_run)
        raw_cands = run_sift(args.schedule_block)
        unique_heads, known_matched = run_known_sources(args.schedule_block)
        info = {
            'schedule_block': args.schedule_block,
            'start_time': start_time,
            'raw_cands': raw_cands,
            'unique_heads': unique_heads,
            'known_matched': known_matched
        }
        send_notification(info)

    elif args.mode == "sift":
        run_sift(args.schedule_block)

    elif args.mode == "parameters":
        run_parameters(args.schedule_block)

    log.info("All done.")


if __name__ == "__main__":
    main()
