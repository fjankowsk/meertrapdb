# -*- coding: utf-8 -*-
#
#   2018 - 2019 Fabian Jankowski
#   Database schema classes.
#

from __future__ import print_function
from datetime import datetime
from decimal import Decimal
from pony.orm import (Database, PrimaryKey, Optional, Required, Set)


db = Database()


class ScheduleBlock(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    sb_id = Required(int, size=64, unsigned=True)
    sb_id_code = Required(str, max_len=32)
    proposal_id = Optional(str, max_len=32)
    proj_main = Required(str, max_len=16)
    proj = Required(str, max_len=16)
    #utc_start = Required(datetime, precision=6)
    utc_start = Required(datetime, precision=0)
    observer = Optional(str, max_len=16)
    description = Optional(str, max_len=128)
    observation = Set('Observation')


class Observation(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    schedule_block = Set('ScheduleBlock')
    field_name = Required(str, max_len=32)
    boresight_ra = Required(str, max_len=32)
    boresight_dec = Required(str, max_len=32)
    #utc_start = Required(datetime, precision=6)
    #utc_end = Required(datetime, precision=6)
    #utc_added = Required(datetime, precision=6, sql_default='CURRENT_TIMESTAMP')
    utc_start = Required(datetime, precision=0)
    utc_end = Required(datetime, precision=0)
    utc_added = Required(datetime, precision=0, default=datetime.utcnow())
    tobs = Required(float)
    finished = Required(bool)
    nant = Required(int, size=8, unsigned=True)
    receiver = Required(int, size=8, unsigned=True)
    cfreq = Required(float)
    bw = Required(float)
    nchan = Required(int, size=16, unsigned=True)
    npol = Required(int, size=8, unsigned=True)
    tsamp = Required(float)
    beam_config = Set('BeamConfig')
    sps_candidate = Set('SpsCandidate')
    #tuse_status = Set('TuseStatus')
    #fbfuse_status = Set('FbfuseStatus')
    logs = Set('Logs')
    notes = Optional(str, max_len=256)


class BeamConfig(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    nbeam = Required(int, size=16, unsigned=True)
    tiling_mode = Required(str, max_len=32)
    observation = Set('Observation')


class Beam(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    number = Required(int, size=16, unsigned=True, index=True)
    coherent = Required(bool)
    source = Required(str, max_len=32)
    ra = Required(str, max_len=32)
    dec = Required(str, max_len=32)
    gl = Required(float)
    gb = Required(float)
    sps_candidate = Set('SpsCandidate')


""" class TuseStatus(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    status = Required(str, max_len=32)
    description = Optional(str, max_len=64)
    obs = Set('Observation') """


""" class FbfuseStatus(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    status = Required(str, max_len=32)
    description = Optional(str, max_len=64)
    obs = Set('Observation') """


""" class PeriodCandidate(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    utc = Required(datetime, precision=6)
    utc_added = Required(datetime, precision=6, sql_default='CURRENT_TIMESTAMP')
    obs = Set('Observation')
    ra = Required(str, max_len=32)
    dec = Required(str, max_len=32)
    beam = Required(int, size=16, unsigned=True)
    snr = Required(float)
    period = Required(float)
    dm = Required(float)
    width = Required(float)
    acc = Required(float)
    node = Set('Node')
    dynamic_spectrum = Required(str, max_len=2048)
    profile = Required(str, max_len=2048)
    dmcurve = Required(str, max_len=2048)
    score = Required(float)
    pipeline_config = Set('PipelineConfig')
    classifier_config = Set('ClassifierConfig') """


class SpsCandidate(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    # utc = Required(datetime, precision=6)
    # utc_added = Required(datetime, precision=6, sql_default='CURRENT_TIMESTAMP')
    utc = Required(str, max_len=32)
    #utc_added = Required(datetime, precision=6, sql_default='CURRENT_TIMESTAMP')
    utc_added = Required(datetime, precision=0, default=datetime.utcnow())
    mjd = Required(Decimal, precision=13, scale=8)
    observation = Set('Observation')
    beam = Set('Beam')
    snr = Required(float)
    dm = Required(float)
    dm_ex = Required(float)
    width = Required(float)
    node = Set('Node')
    dynamic_spectrum = Required(str, max_len=2048)
    profile = Required(str, max_len=2048)
    heimdall_plot = Required(str, max_len=2048)
    #score = Required(float)
    viewed = Optional(int, size=16, unsigned=True, default=0)
    pipeline_config = Set('PipelineConfig')
    #classifierconfig = Set('ClassifierConfig')


class Node(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    number = Required(int, size=8, unsigned=True)
    hostname = Required(str, max_len=64)
    #periodcandidate = Set('PeriodCandidate')
    sps_candidate = Set('SpsCandidate')
    logs = Set('Logs')


class PipelineConfig(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    name = Required(str, max_len=32)
    version = Required(str, max_len=32)
    dd_plan = Required(str, max_len=512)
    dm_threshold = Required(float)
    snr_threshold = Required(float)
    width_threshold = Required(float)
    zerodm_zapping = Required(bool)
    #period_candidate = Set('PeriodCandidate')
    sps_candidate = Set('SpsCandidate')


""" class ClassifierConfig(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    name = Required(str, max_len=32)
    version = Required(str, max_len=32)
    period_candidate = Set('PeriodCandidate')
    sps_candidate = Set('SpsCandidate') """


class Logs(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    #utc = Required(datetime, precision=6)
    #utc_added = Required(datetime, precision=6, sql_default='CURRENT_TIMESTAMP')
    utc = Required(datetime, precision=0)
    utc_added = Required(datetime, precision=0, default=datetime.utcnow())
    obs = Set('Observation')
    program = Required(str, max_len=32)
    process = Required(str, max_len=32)
    logger = Required(str, max_len=32)
    module = Required(str, max_len=32)
    level = Required(int, size=8, unsigned=True)
    message = Required(str, max_len=512)
    node = Set('Node')


""" class Benchmark(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    utc = Required(datetime, precision=6)
    utc_added = Required(datetime, precision=6, sql_default='CURRENT_TIMESTAMP')
    nproc = Required(int, size=8, unsigned=True)
    nobs = Required(int, size=64, unsigned=True)
    nsps = Required(int, size=64, unsigned=True)
    nperiod = Required(int, size=64, unsigned=True)
    dt = Required(float)
    dobs = Required(float)
    dsps = Required(float)
    dperiod = Required(float) """
