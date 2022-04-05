#
#   2019 - 2020 Fabian Jankowski
#   Slack related helper functions.
#

import json
import logging
import requests as req
import sys
import time

from meertrapdb.config_helpers import get_config


def send_slack_notification(info):
    """
    Send notification to Slack.

    Parameters
    ----------
    info: dict
        All parameters for the Slack message.
    """

    log = logging.getLogger("meertrapdb.slack_helpers")
    config = get_config()
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

    text = "SB: {0}, start date: {1}, raw candidates: {2}, unique heads: {3}, unmatched unique heads: {4}".format(
        info["schedule_block"],
        info["start_time"],
        info["raw_cands"],
        info["unique_heads"],
        info["unique_heads"] - info["known_matched"],
    )

    message = {
        "pretext": "* {0} NEW SB injected:* \n".format(current_time),
        "color": config["notifier"]["colour"],
        "text": text,
    }

    cand_message = {"attachments": [message]}
    message_json = json.dumps(cand_message)

    try:
        req.post(config["notifier"]["http_link"], data=message_json, timeout=2)
    except Exception:
        log.error("Something happened when trying to send the data to Slack.")
        log.error(sys.exc_info()[0])
