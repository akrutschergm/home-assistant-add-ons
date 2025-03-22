from argparse import ArgumentParser
import asyncio
from datetime import time
import services.core
import services.filewatcher
import services.timer
import adapter.tado
import logging, logging.handlers
from models.settings import CoreSettings
import sys, time


def create_file_log_handler(log_file: str = None) -> logging.Handler:
    """Configures a daily rotating file logging handler with the given file name.

    Args:
        log_file (str, optional): The name of the log file. Defaults to None.

    Returns:
        logging.Handler: A configured logging handler.
    """
    return configure_log_handler(
        logging.handlers.TimedRotatingFileHandler(log_file, when='d', backupCount=7, encoding='utf-8'))

def create_console_log_handler() -> logging.Handler:
    """Configures a console logging handler.

    Returns:
        logging.Handler: A configured logging handler.
    """
    return configure_log_handler(
        logging.StreamHandler()) # log to stderr

def configure_log_handler(log_handler: logging.Handler) -> logging.Handler:
    """Sets a logging Formatter for the given logging handler.

    Args:
        log_handler (logging.Handler): A logging handler which should be configured with a formatter.

    Returns:
        logging.Handler: A configured logging handler.
    """
    formatter = logging.Formatter(fmt='%(asctime)s %(name)s %(levelname)s - %(message)s', datefmt='%b %d %H:%M:%S')
    log_handler.setFormatter(formatter)

    return log_handler


async def main(argv):

    logging_argparse = ArgumentParser(prog=__file__, add_help=False)
    logging_argparse.add_argument('--log-level', default='INFO', help='set log level')
    logging_argparse.add_argument('-l', '--log-file', help='set log file')
    logging_args, _ = logging_argparse.parse_known_args(argv)

    try:
        log_level = logging_args.log_level
    except ValueError:
        logging.error("Invalid log level: {}".format(logging_args.log_level))
        sys.exit(1)

    log_file = logging_args.log_file

    if log_file:
        logging.basicConfig(handlers = [ create_file_log_handler(log_file),
                                         create_console_log_handler() ],
                            level = log_level)
    else:
        logging.basicConfig(handlers = [ create_console_log_handler() ], level = log_level)

    logger = logging.getLogger(__name__)
    logger.info('Starting')
    logger.info("Log level set: {}".format(logging.getLevelName(logger.getEffectiveLevel())))

    parsers = [logging_argparse]
    main_parser = ArgumentParser(prog=__file__, parents=parsers)
    main_parser.add_argument('-c', '--config-file')
    main_args = main_parser.parse_args(argv)

    config_file = main_args.config_file

    logger.info("Config file is: {}".format(config_file))

    try:
        # Create a queue that we will use to store our "workload".
        queue = asyncio.Queue()

        config = CoreSettings.load_from(config_file)
        polling_minutes = config.churchtools.resources_polling_minutes

        tado = adapter.tado.TadoAdapter()

        async with asyncio.TaskGroup() as tg:
            # Save a reference to the result of this function, otherwise it may get
            # garbage collected at any time, even before it’s done
            core_task = tg.create_task(
                services.core.Service(config_file, queue, tado)
                .run())

            timer_task = tg.create_task(
                services.timer.Service(polling_minutes, queue, message = services.core.Message())
                .run())

            config_file_changes_task = tg.create_task(
                services.filewatcher.Service(config_file, queue, message = services.core.Message(config_changed = True))
                .run())

            logger.info("Started at %s", time.strftime('%X'))

            # queue.put_nowait(services.core.Message())

    except asyncio.CancelledError:
        logger.info("Exited at %s", time.strftime('%X'))

    except Exception as e:
        logger.critical(e)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
