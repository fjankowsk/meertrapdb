/*
detail view
*/

SELECT spscandidate.utc, spscandidate.snr, spscandidate.dm, spscandidate.width,
observation.field_name, beam.number, beam.coherent, scheduleblock.sb_id_code
FROM spscandidate

LEFT JOIN observation_spscandidate
ON spscandidate.id=observation_spscandidate.spscandidate
LEFT JOIN observation
ON observation_spscandidate.observation=observation.id

LEFT JOIN beam_spscandidate
ON spscandidate.id=beam_spscandidate.spscandidate
LEFT JOIN beam
ON beam_spscandidate.beam=beam.id

LEFT JOIN observation_scheduleblock
ON observation.id=observation_scheduleblock.observation
LEFT JOIN scheduleblock
ON observation_scheduleblock.scheduleblock=scheduleblock.id

WHERE spscandidate.id=1
ORDER BY spscandidate.snr DESC;

/*
grid and overview
*/

SELECT spscandidate.utc, spscandidate.snr, spscandidate.dm, spscandidate.width,
observation.field_name, beam.number, beam.coherent, scheduleblock.sb_id_code
from spscandidate

LEFT JOIN observation_spscandidate
ON spscandidate.id=observation_spscandidate.spscandidate
LEFT JOIN observation
ON observation_spscandidate.observation=observation.id

LEFT JOIN beam_spscandidate
ON spscandidate.id=beam_spscandidate.spscandidate
LEFT JOIN beam
ON beam_spscandidate.beam=beam.id

LEFT JOIN observation_scheduleblock
ON observation.id=observation_scheduleblock.observation
LEFT JOIN scheduleblock
ON observation_scheduleblock.scheduleblock=scheduleblock.id

WHERE scheduleblock.id=1
AND observation.id=1
AND beam.number between 123 and 160
ORDER BY spscandidate.snr DESC
LIMIT 100 OFFSET 200;
