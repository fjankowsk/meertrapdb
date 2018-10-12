USE test;

CREATE TABLE IF NOT EXISTS `BeamConfig` (
  `configid` int(10) unsigned NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`configid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `FbfuseStatus` (
  `statusid` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `description` varchar(64) NOT NULL DEFAULT '',
  PRIMARY KEY (`statusid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `LogTypes` (
  `typeid` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `description` varchar(64) NOT NULL DEFAULT '',
  PRIMARY KEY (`typeid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `NodeList` (
  `nodeid` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `ip` varchar(15) NOT NULL DEFAULT '',
  `hostname` varchar(64) NOT NULL DEFAULT '',
  PRIMARY KEY (`nodeid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `TilingStrategy` (
  `strategyid` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `mainproj` varchar(16) NOT NULL DEFAULT '',
  PRIMARY KEY (`strategyid`),
  UNIQUE KEY `mainproj` (`mainproj`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `TuseStatus` (
  `statusid` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `description` varchar(64) NOT NULL DEFAULT '',
  PRIMARY KEY (`statusid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `Observations` (
  `obsid` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `ra` float NOT NULL,
  `dec` float NOT NULL,
  `mainproj` varchar(16) NOT NULL DEFAULT '',
  `proj` varchar(16) NOT NULL DEFAULT '',
  `observer` varchar(16) NOT NULL DEFAULT '',
  `utcstart` datetime NOT NULL,
  `utcend` datetime NOT NULL,
  `utcadded` datetime NOT NULL,
  `finished` tinyint(3) unsigned NOT NULL,
  `nant` mediumint(8) unsigned NOT NULL,
  `cfreq` float NOT NULL,
  `bw` float NOT NULL,
  `npol` tinyint(3) unsigned NOT NULL,
  `tsamp` float NOT NULL,
  `beamconfig` int(10) unsigned NOT NULL,
  `tuse_status` mediumint(8) unsigned NOT NULL,
  `fbfuse_status` mediumint(8) unsigned NOT NULL,
  PRIMARY KEY (`obsid`),
  KEY `tuse_status` (`tuse_status`),
  KEY `fbfuse_status` (`fbfuse_status`),
  KEY `beamconfig` (`beamconfig`),
  CONSTRAINT `observations_ibfk_1` FOREIGN KEY (`tuse_status`) REFERENCES `TuseStatus` (`statusid`),
  CONSTRAINT `observations_ibfk_2` FOREIGN KEY (`fbfuse_status`) REFERENCES `FbfuseStatus` (`statusid`),
  CONSTRAINT `observations_ibfk_3` FOREIGN KEY (`beamconfig`) REFERENCES `BeamConfig` (`configid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `PipelineLogs` (
  `logid` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `utc` datetime NOT NULL,
  `program` varchar(32) NOT NULL DEFAULT '',
  `type` mediumint(8) unsigned NOT NULL,
  `message` varchar(512) NOT NULL DEFAULT '',
  `nodeid` mediumint(8) unsigned NOT NULL,
  PRIMARY KEY (`logid`),
  KEY `nodeid` (`nodeid`),
  KEY `type` (`type`),
  CONSTRAINT `pipelinelogs_ibfk_1` FOREIGN KEY (`logid`) REFERENCES `Observations` (`obsid`),
  CONSTRAINT `pipelinelogs_ibfk_2` FOREIGN KEY (`nodeid`) REFERENCES `NodeList` (`nodeid`),
  CONSTRAINT `pipelinelogs_ibfk_3` FOREIGN KEY (`type`) REFERENCES `LogTypes` (`typeid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `PeriodCandidates` (
  `periodcandid` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `utc` datetime NOT NULL,
  `utcadded` datetime NOT NULL,
  `pointing` int(10) unsigned NOT NULL,
  `snr` float NOT NULL,
  `period` float NOT NULL,
  `dm` float NOT NULL,
  `width` float NOT NULL,
  `nodeid` mediumint(8) unsigned NOT NULL,
  `dynamicspectrum` blob NOT NULL,
  `profile` blob NOT NULL,
  `dmcurve` blob NOT NULL,
  PRIMARY KEY (`periodcandid`),
  KEY `nodeid` (`nodeid`),
  CONSTRAINT `periodcandidates_ibfk_1` FOREIGN KEY (`periodcandid`) REFERENCES `Observations` (`obsid`),
  CONSTRAINT `periodcandidates_ibfk_2` FOREIGN KEY (`nodeid`) REFERENCES `NodeList` (`nodeid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `SpsCandidates` (
  `spscandid` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `utc` datetime NOT NULL,
  `utcadded` datetime NOT NULL,
  `pointing` int(10) unsigned NOT NULL,
  `ra` float NOT NULL,
  `dec` float NOT NULL,
  `snr` float NOT NULL,
  `dm` float NOT NULL,
  `width` float NOT NULL,
  `nodeid` mediumint(8) unsigned NOT NULL,
  `dynamicspectrum` blob NOT NULL,
  `profile` blob NOT NULL,
  PRIMARY KEY (`spscandid`),
  KEY `nodeid` (`nodeid`),
  CONSTRAINT `spscandidates_ibfk_1` FOREIGN KEY (`spscandid`) REFERENCES `Observations` (`obsid`),
  CONSTRAINT `spscandidates_ibfk_2` FOREIGN KEY (`nodeid`) REFERENCES `NodeList` (`nodeid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;