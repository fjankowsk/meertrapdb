# -*- coding: utf-8 -*-
#
#   2018 - 2019 Fabian Jankowski
#   Schema classes for database benchmark.
#

from __future__ import print_function
from datetime import datetime
from decimal import Decimal
from pony.orm import (Database, PrimaryKey, Optional, Required, Set)


db = Database()


class Benchmark(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    utc = Required(datetime, precision=6)
    utc_added = Required(datetime, precision=0, default=datetime.utcnow())
    nproc = Required(int, size=8, unsigned=True)
    nobs = Required(int, size=64, unsigned=True)
    nsps = Required(int, size=64, unsigned=True)
    nperiod = Required(int, size=64, unsigned=True)
    dt = Required(float)
    dobs = Required(float)
    dsps = Required(float)
    dperiod = Required(float)


class ClassifierConfig(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    name = Required(str, max_len=32)
    version = Required(str, max_len=32)
    period_candidate = Set('PeriodCandidate')
    sps_candidate = Set('SpsCandidate')


class PeriodCandidate(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    utc = Required(datetime, precision=6)
    utc_added = Required(datetime, precision=0, default=datetime.utcnow())
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
    dynamic_spectrum = Optional(str, max_len=2048)
    profile = Optional(str, max_len=2048)
    dmcurve = Optional(str, max_len=2048)
    score = Required(float)
    pipeline_config = Set('PipelineConfig')
    classifier_config = Set('ClassifierConfig')
