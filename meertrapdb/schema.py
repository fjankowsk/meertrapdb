# -*- coding: utf-8 -*-
#
#   2018 - 2019 Fabian Jankowski
#   Database schema classes.
#

from __future__ import print_function
from datetime import datetime
from pony.orm import (Database, PrimaryKey, Optional, Required, Set)


db = Database()

class Observation(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    ra = Required(float)
    dec = Required(float)
    mainproj = Required(str, max_len=16)
    proj = Required(str, max_len=16)
    observer = Required(str, max_len=16)
    utcstart = Required(datetime, precision=6)
    utcend = Required(datetime, precision=6)
    utcadded = Required(datetime, precision=6, sql_default='CURRENT_TIMESTAMP')
    tobs = Required(float)
    finished = Required(bool)
    nant = Required(int, unsigned=True, size=8)
    cfreq = Required(float)
    bw = Required(float)
    npol = Required(int, unsigned=True, size=8)
    tsamp = Required(float)
    beamconfig = Set('BeamConfig')
    tuse_status = Set('TuseStatus')
    fbfuse_status = Set('FbfuseStatus')
    periodcandidate = Set('PeriodCandidate')
    spscandidate = Set('SpsCandidate')
    logs = Set('Logs')
    notes = Optional(str, max_len=128)

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
    utcadded = Required(datetime, precision=6, sql_default='CURRENT_TIMESTAMP')
    obs = Set('Observation')
    ra = Required(float)
    dec = Required(float)
    beam = Required(str, max_len=8)
    snr = Required(float)
    period = Required(float)
    dm = Required(float)
    width = Required(float)
    acc = Required(float)
    node = Set('Node')
    dynamicspectrum = Required(buffer)
    profile = Required(buffer)
    dmcurve = Required(buffer)
    score = Required(float)
    pipelineconfig = Set('PipelineConfig')
    classifierconfig = Set('ClassifierConfig')

class SpsCandidate(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    utc = Required(datetime, precision=6)
    utcadded = Required(datetime, precision=6, sql_default='CURRENT_TIMESTAMP')
    obs = Set('Observation')
    ra = Required(float)
    dec = Required(float)
    beam = Required(str, max_len=8)
    snr = Required(float)
    dm = Required(float)
    width = Required(float)
    node = Set('Node')
    dynamicspectrum = Required(buffer)
    profile = Required(buffer)
    score = Required(float)
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
    snr_threshold = Required(float)
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
    utcadded = Required(datetime, precision=6, sql_default='CURRENT_TIMESTAMP')
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
