#
#   2020 Fabian Jankowski
#   Search for detections of known sources.
#

from pony.orm import db_session, select, count, desc

from meertrapdb import schema
from meertrapdb.schema import db
from meertrapdb.config_helpers import get_config


#
# MAIN
#


def main():
    config = get_config()
    dbconf = config["db"]

    db.bind(
        provider=dbconf["provider"],
        host=dbconf["host"],
        port=dbconf["port"],
        user=dbconf["user"]["name"],
        passwd=dbconf["user"]["password"],
        db=dbconf["database"],
    )
    db.generate_mapping(create_tables=False)

    with db_session:
        query1 = select(
            (ks.id, ks.name, ks.source_type, ks.dm, count(c))
            for ks in schema.KnownSource
            for c in ks.sps_candidate
            for sr in c.sift_result
            if "RRAT" in ks.source_type
            and c.snr > 8.0
            and c.width > 1.0
            and c.width < 50.0
            and sr.is_head == True
            and sr.beams < 50
        ).order_by(lambda idx, name, stype, dm, cnt: desc(cnt))

        query1.show()
        print(query1.count())


if __name__ == "__main__":
    main()
