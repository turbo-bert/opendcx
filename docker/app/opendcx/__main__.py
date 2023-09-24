import os
import sys
import os.path
import logging
import json
import time
import traceback

from selenium.webdriver.firefox.options import Options as FFOptions
from selenium import webdriver

from selenium.webdriver.common.keys import Keys as KEYS
from selenium.webdriver.common.by import By as BY

from selenium.webdriver.support.ui import WebDriverWait as WDW
from selenium.webdriver.support.ui import Select as SEL
from selenium.webdriver.support import expected_conditions as EC


class Context:

    def __init__(self) -> None:
        self._playbook = '/work/playbook.js'
        self._playbook_data = None
        self._playbookenv = '/work/env.js'
        self._playbookenv_data = None
        self._odir = '/work/run-%d' % (int) (time.time())
        self._logfile_debug = os.path.join(self._odir, 'log_debug.txt')
        self._logfile_info = os.path.join(self._odir, 'log_info.txt')
        self._logfile_error = os.path.join(self._odir, 'log_error.txt')
        self._log_format = '%(asctime)s [%(levelname)-10s] %(message)s'

    def load(self) -> None:
        os.makedirs(self._odir, exist_ok=False)
        os.makedirs(os.path.join(self._odir, 'build', 'org'), exist_ok=False)
        os.makedirs(os.path.join(self._odir, 'build', '_', 'screenshots'), exist_ok=False)
        os.makedirs(os.path.join(self._odir, 'downloads'), exist_ok=False)

        self.setup_logging()
        logging.info(self._logfile_error)
        logging.debug("context loading...")
        if os.path.isfile(self._playbook):
            logging.debug("loading playbook")
            self._playbook_data = json.loads(open(self._playbook, 'r').read())
            logging.info(self._playbook_data)
        else:
            logging.error("unable to find playbook")
            sys.exit(1)
        if os.path.isfile(self._playbookenv):
            logging.debug("loading playbook env")
            self._playbookenv_data = json.loads(open(self._playbookenv, 'r').read())
            logging.info(self._playbookenv_data)
    
    def setup_logging(self) -> None:
        self._root_logger = logging.getLogger()
        self._root_logger.setLevel(logging.DEBUG)
        self._root_logger.propagate = False
        
        self._logger_debug = logging.FileHandler(self._logfile_debug)
        self._logger_debug.setLevel(logging.DEBUG)
        self._logger_debug.setFormatter(logging.Formatter(self._log_format))
        self._root_logger.addHandler(self._logger_debug)

        self._logger_info = logging.FileHandler(self._logfile_info)
        self._logger_info.setLevel(logging.INFO)
        self._logger_info.setFormatter(logging.Formatter(self._log_format))
        self._root_logger.addHandler(self._logger_info)

        self._logger_error = logging.FileHandler(self._logfile_error)
        self._logger_error.setLevel(logging.ERROR)
        self._logger_error.setFormatter(logging.Formatter(self._log_format))
        self._root_logger.addHandler(self._logger_error)

        self._logger_stderror = logging.StreamHandler(sys.stderr)
        if os.getenv("OPENDCX_VERBOSE", "0") == "1":
            self._logger_stderror.setLevel(logging.INFO)
        else:
            self._logger_stderror.setLevel(logging.ERROR)
        self._logger_stderror.setFormatter(logging.Formatter(self._log_format))
        self._root_logger.addHandler(self._logger_stderror)


    def connect_selenium_remote(self) -> None:
        self._ffoptions = FFOptions()
        self._driver: webdriver.Remote
        self._driver = None
        self._selenium_host = os.getenv("OPENDCX_SELENIUM_HOST", "host.docker.internal")
        self._selenium_port = os.getenv("OPENDCX_SELENIUM_PORT", "4444")
        try:
            self._driver = webdriver.Remote(command_executor='http://%s:%s/wd/hub' % (self._selenium_host, self._selenium_port), options=self._ffoptions)
            logging.info("connected driver")
        except:
            logging.error("unable to connect driver")
            sys.exit(1)

    def disconnect_selenium_remote(self) -> None:
        logging.info("will disconnect driver")
        self._driver.quit()

context = Context()
context.load()
context.connect_selenium_remote()
context.disconnect_selenium_remote()
