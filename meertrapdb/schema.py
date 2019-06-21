# -*- coding: utf-8 -*-
#
#   2018 - 2019 Fabian Jankowski
#   Database schema classes.
#

from __future__ import print_function
from datetime import datetime
from pony.orm import (Database, Decimal, PrimaryKey, Optional, Required, Set)


db = Database()

class Observation(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    sb_id = Required(int, size=64, unsigned=True)
    sb_id_code = Required(str, max_len=32)
    boresight_ra = Required(str, max_len=32)
    boresight_dec = Required(str, max_len=32)
    mainproj = Required(str, max_len=16)
    proj = Required(str, max_len=16)
    observer = Required(str, max_len=16)
    utc_start = Required(datetime, precision=6)
    utc_end = Required(datetime, precision=6)
    utc_added = Required(datetime, precision=6, sql_default='CURRENT_TIMESTAMP')
    tobs = Required(float)
    finished = Required(bool)
    nant = Required(int, size=8, unsigned=True)
    cfreq = Required(float)
    bw = Required(float)
    npol = Required(int, size=8, unsigned=True)
    tsamp = Required(float)
    beamconfig = Set('BeamConfig')
    tuse_status = Set('TuseStatus')
    fbfuse_status = Set('FbfuseStatus')
    periodcandidate = Set('PeriodCandidate')
    spscandidate = Set('SpsCandidate')
    logs = Set('Logs')
    notes = Optional(str, max_len=256)

class BeamConfig(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    nbeam = Required(int, size=16, unsigned=True)
    tilingmode = Required(str, max_len=32)
    obs = Set('Observation')

class TuseStatus(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    status = Required(str, max_len=32)
    description = Optional(str, max_len=64)
    obs = Set('Observation')

class FbfuseStatus(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    status = Required(str, max_len=32)
    description = Optional(str, max_len=64)
    obs = Set('Observation')

class PeriodCandidate(db.Entity):
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
    dynamicspectrum = Required(str, max_len=2048)
    profile = Required(str, max_len=2048)
    dmcurve = Required(str, max_len=2048)
    score = Required(float)
    pipelineconfig = Set('PipelineConfig')
    classifierconfig = Set('ClassifierConfig')

class SpsCandidate(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    utc = Required(datetime, precision=6)
    utc_added = Required(datetime, precision=6, sql_default='CURRENT_TIMESTAMP')
    mjd = Required(Decimal, precision=13, scale=8)
    obs = Set('Observation')
    beam = Required(int, size=16, unsigned=True)
    snr = Required(float)
    dm = Required(float)
    dm_ex = Required(float)
    width = Required(float)
    ra = Required(str, max_len=32)
    dec = Required(str, max_len=32)
    gl = Required(float)
    gb = Required(float)
    node = Set('Node')
    dynamicspectrum = Required(str, max_len=2048)
    profile = Required(str, max_len=2048)
    heimdall_plot = Required(str, max_len=2048)
    score = Required(float)
    viewed = Optional(int, size=10, unsigned=True, default=0)
    pipelineconfig = Set('PipelineConfig')
    classifierconfig = Set('ClassifierConfig')

class Node(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    ip = Required(str, max_len=16)
    hostname = Required(str, max_len=64)
    periodcandidate = Set('PeriodCandidate')
    spscandidate = Set('SpsCandidate')
    logs = Set('Logs')

class PipelineConfig(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    name = Required(str, max_len=32)
    version = Required(str, max_len=32)
    ddplan = Required(str, max_len=512)
    dm_threshold = Required(float)
    snr_threshold = Required(float)
    width_threshold = Required(float)
    zerodm_zapping = Required(bool)
    periodcandidate = Set('PeriodCandidate')
    spscandidate = Set('SpsCandidate')

class ClassifierConfig(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    name = Required(str, max_len=32)
    version = Required(str, max_len=32)
    periodcandidate = Set('PeriodCandidate')
    spscandidate = Set('SpsCandidate')

class Logs(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    utc = Required(datetime, precision=6)
    utc_added = Required(datetime, precision=6, sql_default='CURRENT_TIMESTAMP')
    obs = Set('Observation')
    program = Required(str, max_len=32)
    process = Required(str, max_len=32)
    logger = Required(str, max_len=32)
    module = Required(str, max_len=32)
    level = Required(int, size=8)
    message = Required(str, max_len=512)
    node = Set('Node')

class Benchmark(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    utc = Required(datetime, precision=6)
    utcadded = Required(datetime, precision=6, sql_default='CURRENT_TIMESTAMP')
    nproc = Required(int, size=8)
    nobs = Required(int, size=64)
    nsps = Required(int, size=64)
    nperiod = Required(int, size=64)
    dt = Required(float)
    dobs = Required(float)
    dsps = Required(float)
    dperiod = Required(float)
