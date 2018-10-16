# -*- coding: utf-8 -*-
#
#   2018 Fabian Jankowski
#   Test the database.
#

from __future__ import print_function
import argparse
from datetime import datetime
import logging
from multiprocessing import Pool
from operator import attrgetter
import signal
import sys
from time import sleep
import pony.orm as pn
from pony.orm import db_session
# local ones
from config_helpers import get_config
from db_helpers import setup_db
from schema import (db, Observation, BeamConfig, TuseStatus,
                    FbfuseStatus, PeriodCandidate, SpsCandidate,
                    Node, PipelineConfig, ClassifierConfig)

# version info
__version__ = "$Revision$"

def insert_data(task):
    """
    Insert data into the database.
    """

    config = get_config()
    pconf = config['pipeline']

    log = logging.getLogger('meertrapdb')

    while True:
        now = datetime.now()
        buf = b'jfdsajlkfdsjlafjaklsfjladksflkdsjfklsjflkas'
        
        with db_session:
            fbfusestatus = FbfuseStatus(
                status='good',
                description='all fine'
            )

            tusestatus = TuseStatus(
                status='good',
                description='all fine'
            )

            beamconfig = BeamConfig(
                nbeam=396,
                tilingmode='fill'
            )

            obs = Observation(
                ra=0,
                dec=0,
                mainproj="Bla",
                proj="bdfsa",
                observer="Fabian",
                utcstart=now,
                utcend=now,
                utcadded=now,
                tobs=360.0,
                finished=False,
                nant=64,
                cfreq=1400.123,
                bw=800.0,
                npol=1,
                tsamp=0.1234,
                beamconfig=beamconfig,
                fbfuse_status=fbfusestatus,
                tuse_status=tusestatus
            )

            node1 = Node(
                ip='192.168.1.123',
                hostname='compute123.meertrap.local'
            )

            node2 = Node(
                ip='192.168.1.198',
                hostname='compute198.meertrap.local'
            )

            pipelineconfig = PipelineConfig(
                name='Cheetah',
                version='0.7.5',
                ddplan='Blablabla',
                snr_threshold=7.5,
                zerodm_zapping=True
            )

            classifierconfig = ClassifierConfig(
                name='AwesomeClassifier',
                version='0.2.5'
            )

            for _ in range(500):
                SpsCandidate(
                    utc=now,
                    utcadded=now,
                    ra=0.0,
                    dec=0.0,
                    beam='in0',
                    snr=9.5,
                    dm=1234.56,
                    width=2.7,
                    dynamicspectrum=buf,
                    profile=buf,
                    score=97.3,
                    obs=obs,
                    node=node1,
                    pipelineconfig=pipelineconfig,
                    classifierconfig=classifierconfig
                )
            
            for _ in range(200):
                PeriodCandidate(
                    utc=now,
                    utcadded=now,
                    ra=0.0,
                    dec=0.0,
                    beam='in0',
                    snr=9.5,
                    period=89.123,
                    dm=1234.56,
                    width=2.7,
                    acc=100.0,
                    dynamicspectrum=buf,
                    profile=buf,
                    dmcurve=buf,
                    score=97.3,
                    obs=obs,
                    node=node2,
                    pipelineconfig=pipelineconfig,
                    classifierconfig=classifierconfig
                )

        log.debug("Done. Time taken: {0}".format(datetime.now() - now))
        #sleep(pconf['sps']['interval'])


def run_benchmark(nproc):
    """
    Benchmark concurrent database connections.
    """

    log = logging.getLogger('meertrapdb')

    p = Pool(processes=nproc)
    tasks = [500 for _ in range(nproc)]

    p.map_async(insert_data, tasks)

    nobs = 0
    nsps = 0
    nperiod = 0
    now = datetime.now()

    while True:
        with db_session:
            tobs = pn.max(o.id for o in Observation)
            tsps = pn.max(o.id for o in SpsCandidate)
            tperiod = pn.max(o.id for o in PeriodCandidate)

        if tobs is not None \
        and tsps is not None \
        and tperiod is not None:
            dt = (datetime.now() - now).total_seconds()
            dobs = (tobs - nobs)/dt
            dsps = (tsps - nsps)/dt
            dperiod = (tperiod - nperiod)/dt

            log.info("Dt, dObs, dSps, dPeriod [1/s]: {0:.1f} s, {1:.1f}, {2:.1f}, {3:.1f}".format(
                dt, dobs, dsps, dperiod))
        
            nobs = tobs
            nsps = tsps
            nperiod = tperiod
            now = datetime.now()

        sleep(10)


def run_test():
    """
    Test the database.
    """

    log = logging.getLogger('meertrapdb')

    with db_session:
        #print(Observation.describe())
        #Observation.select().show()

        #pn.select((o.utcstart,o.cfreq,o.bw) for o in Observation).show()
        log.info(pn.count(o.id for o in Observation))

    now = datetime.now()
    buf = b'jfdsajlkfdsjlafjaklsfjladksflkdsjfklsjflkas'

    with db_session:
        fbfusestatus = FbfuseStatus(
            status='good',
            description='all fine'
        )

        tusestatus = TuseStatus(
            status='good',
            description='all fine'
        )

        beamconfig = BeamConfig(
            nbeam=396,
            tilingmode='fill'
        )

        obs = Observation(
            ra=0,
            dec=0,
            mainproj="Bla",
            proj="bdfsa",
            observer="Fabian",
            utcstart=now,
            utcend=now,
            utcadded=now,
            tobs=360.0,
            finished=False,
            nant=64,
            cfreq=1400.123,
            bw=800.0,
            npol=1,
            tsamp=0.1234,
            beamconfig=beamconfig,
            fbfuse_status=fbfusestatus,
            tuse_status=tusestatus
        )

        node1 = Node(
            ip='192.168.1.123',
            hostname='compute123.meertrap.local'
        )

        node2 = Node(
            ip='192.168.1.198',
            hostname='compute198.meertrap.local'
        )

        pipelineconfig = PipelineConfig(
            name='Cheetah',
            version='0.7.5',
            ddplan='Blablabla',
            snr_threshold=7.5,
            zerodm_zapping=True
        )

        classifierconfig = ClassifierConfig(
            name='AwesomeClassifier',
            version='0.2.5'
        )

        for _ in range(500):
            SpsCandidate(
                utc=now,
                utcadded=now,
                ra=0.0,
                dec=0.0,
                beam='in0',
                snr=9.5,
                dm=1234.56,
                width=2.7,
                dynamicspectrum=buf,
                profile=buf,
                score=97.3,
                obs=obs,
                node=node1,
                pipelineconfig=pipelineconfig,
                classifierconfig=classifierconfig
            )
        
        for _ in range(200):
            PeriodCandidate(
                utc=now,
                utcadded=now,
                ra=0.0,
                dec=0.0,
                beam='in0',
                snr=9.5,
                period=89.123,
                dm=1234.56,
                width=2.7,
                acc=100.0,
                dynamicspectrum=buf,
                profile=buf,
                dmcurve=buf,
                score=97.3,
                obs=obs,
                node=node2,
                pipelineconfig=pipelineconfig,
                classifierconfig=classifierconfig
        )


def setup_logging():
    """
    Setup the logging configuration.
    """

    log = logging.getLogger('meertrapdb')

    log.setLevel(logging.DEBUG)
    log.propagate = False

    # log to console
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    fmt = "%(asctime)s, %(processName)s, %(name)s, %(module)s, %(levelname)s: %(message)s"
    console_formatter = logging.Formatter(fmt)
    console.setFormatter(console_formatter)
    log.addHandler(console)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Test the database implementation.")
    
    parser.add_argument(
        'operation',
        choices=['benchmark', 'test'],
        help='Operation that should be performed.')
    
    parser.add_argument(
        '--nproc',
        type=int,
        dest='nproc',
        default=64,
        help='Number of processes that access the database simultanously.')
    
    parser.add_argument(
        "--version",
        action="version",
        version=__version__)

    return parser.parse_args()


#
# MAIN
#

def main():
    args = parse_args()

    log = logging.getLogger('meertrapdb')
    setup_logging()

    try:
        setup_db()
    except pn.dbapiprovider.OperationalError as e:
        log.warn("Could not setup database: {0}".format(str(e)))

    config = get_config()
    dbconf = config['db']

    db.bind(provider=dbconf['provider'],
            host=dbconf['host'],
            user=dbconf['root']['name'],
            passwd=dbconf['root']['password'],
            db='test')

    db.generate_mapping(create_tables=True)

    if args.operation == 'benchmark':
        run_benchmark(nproc=args.nproc)

    elif args.operation == 'test':
        run_test()
    
    log.info("All done.")


if __name__ == "__main__":
    main()