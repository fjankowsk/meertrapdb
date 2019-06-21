import logging

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