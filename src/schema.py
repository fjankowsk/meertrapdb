# -*- coding: utf-8 -*-
#
#   2018 Fabian Jankowski
#   Database schema classes.
#

from __future__ import print_function
from datetime import datetime
import logging
from pony.orm import (Database, PrimaryKey, Optional, Required, Set)
# local ones

# version info
__version__ = "$Revision$"

log = logging.getLogger(__name__)

db = Database()

class Observation(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    ra = Required(float)
    dec = Required(float)
    mainproj = Required(str, max_len=16)
    proj = Required(str, max_len=16)
    observer = Required(str, max_len=16)
    utcstart = Required(datetime)
    utcend = Required(datetime)
    utcadded = Required(datetime)
    finished = Required(bool)
    nant = Required(int, unsigned=True, size=8)
    cfreq = Required(float)
    bw = Required(float)
    npol = Required(int, unsigned=True, size=8)
    tsamp = Required(float)
    beamconfig = Set('BeamConfig')
    tuse_status = Set('TuseStatus')
    fbfuse_status = Set('FbfuseStatus')
    notes = Optional(str, max_len=128)

class BeamConfig(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    nbeam = Required(int, size=16, unsigned=True)
    tilingmode = Required(str, max_len=32)
    obs = Set('Observation')

class TuseStatus(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    status = Required(str, max_len=32)
    description = Required(str, max_len=64)
    obs = Set('Observation')

class FbfuseStatus(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    status = Required(str, max_len=32)
    description = Required(str, max_len=64)
    obs = Set('Observation')

class PeriodCandidate(db.Entity):
    id = PrimaryKey(int, auto=True, size=64, unsigned=True)
    utc = Required(datetime)
    utcadded = Required(datetime)