import os, datetime
import logging, logging.handlers
from pprint import pformat

class _LoggerSingleton:
    instance = None

    class __Logger:

        def __init__(self):
            self.initialized = False
            self.haslogfile = False
            self.verbose = False
            self.logger = None

        def setup(self, args):
            self.initialized = True
            self.verbose = args.verbose or False
            self.logfile = args.logfile or None

            if self.logfile and len(self.logfile) > 0:
                # We also write to a regular TXT log using python's standard library
                loglevel = logging.INFO if not args.verbose else logging.DEBUG
                self.logger = logging.getLogger()

                for hdlr in self.logger.handlers[:]:  # remove all old handlers
                    self.logger.removeHandler(hdlr)

                self.haslogfile = True

                logDir = os.path.dirname(self.logfile)
                if len(logDir) > 0 and not os.path.exists(logDir):
                    os.makedirs(logDir)

                logging.basicConfig(level=loglevel,
                                    filemode='w',
                                    format='%(asctime)s %(levelname)-8s %(message)s',
                                    datefmt='%Y-%m-%d %H:%M:%S',
                                    filename=self.logfile)


        def logprint(self, message, method="", severity="info", exception=None):
            """
            Logprint logs things 3 different ways: 1) stdout 2) log txt file 3) xml
            :param message:
            :param method:
            :param severity:
            :param exception:
            :return:
            """

            # Verbose logs don't get written until we ask for them
            if severity == 'debug' and not self.verbose:
                return

            dateStr = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z')

            if exception is not None:
                txtmsg = '{0}  Exception: {1}'.format(message, str(exception))
                header = '[{0:8s}]  '.format(method) if self.verbose else ""
                msg = '{0}{1} : {2}'.format(header, message.replace("\n", "\n" + header), str(exception))
            else:
                txtmsg = message
                header = '[{0:8s}] '.format(method) if self.verbose else ""
                msg = '{0}{1}'.format(header, message.replace("\n", "\n" + header))

            # Print to stdout
            print msg

            # If we haven't set up a logger then we're done here. Don't write to any files
            if not self.initialized or not self.haslogfile:
                return

            # Write to log file
            if severity == 'info':
                self.logger.info(txtmsg)
            elif severity == 'warning':
                self.logger.warning(txtmsg)
            elif severity == 'error':
                self.logger.error(txtmsg)
            elif severity == 'critical':
                self.logger.critical(txtmsg)
            if severity == 'debug':
                self.logger.debug(txtmsg)


    def __init__(self, **kwargs):
        if not _LoggerSingleton.instance:
            _LoggerSingleton.instance = _LoggerSingleton.__Logger(**kwargs)
    def __getattr__(self, name):
        return getattr(self.instance, name)


class Logger():
    """
    Think of this class like a light interface
    """

    def __init__(self, method=""):
        self.instance = _LoggerSingleton()
        self.method = method

    def setup(self, args):
        self.instance.setup(args)

    def print_(self, message, **kwargs):
        self.instance.logprint(message, **kwargs)

    def debug(self, *args):
        """
        This works a little differently. You can basically throw anything you want into it.
        :param message:
        :return:
        """
        msgarr =  []
        for arg in args:
            msgarr.append(pformat(arg))
        finalmessage = '\n'.join(msgarr).replace('\n', '\n              ')
        self.instance.logprint(finalmessage, self.method, "debug")

    def destroy(self):
        self.instance = None
        self.method = None

    def info(self, message):
        self.instance.logprint(message, self.method, "info")

    def error(self, message, exception=None):
        self.instance.logprint(message, self.method, "error", exception)

    def warning(self, message, exception=None):
        self.instance.logprint(message, self.method, "warning", exception)

    def title(self, msg, sep='-'):
        self.info("\n{0}\n{1}".format(msg, (len(msg) + 2) * sep))


