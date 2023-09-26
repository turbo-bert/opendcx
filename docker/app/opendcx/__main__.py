import os
import sys
import os.path
import logging
import json
import time
import traceback
import subprocess

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
        self._env_map = {} # init during load
        self._cmd_map = {}
        self._cmd_map['get'] = self.exec_get
        self._step_index = 0
        self._orgfile = os.path.join(self._odir, 'build', 'org', 'run.org')

    def load(self) -> None:
        self._step_index = 0
        os.makedirs(self._odir, exist_ok=False)
        os.makedirs(os.path.join(self._odir, 'build', 'org'), exist_ok=False)
        os.makedirs(os.path.join(self._odir, 'build', '_', 'screenshots'), exist_ok=False)
        os.makedirs(os.path.join(self._odir, 'downloads'), exist_ok=False)

        self.setup_logging()
        logging.debug(self._logfile_error)
        logging.debug("context loading...")
        if os.path.isfile(self._playbook):
            logging.debug("loading playbook")
            self._playbook_data = json.loads(open(self._playbook, 'r').read())
        else:
            logging.error("unable to find playbook")
            sys.exit(1)
        if os.path.isfile(self._playbookenv):
            logging.debug("loading playbook env")
            self._playbookenv_data = json.loads(open(self._playbookenv, 'r').read())
            for ek in self._playbookenv_data.keys():
                self._env_map['{{'+ek+'}}'] = self._playbookenv_data[ek]
    
    def next_step(self):
        self._step_index += 1


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

    def stepwalker(self):
        for s in self._playbook_data:
            yield s

    def offyougo(self):
        self.orga("""* Test run step by step""")
        for step_data in context.stepwalker():
            self.next_step()
            self.orga("""** Step %d""" % self._step_index)
            step_id = step_data[0]
            step_cmd = step_data[1]

            step_params = []
            
            if len(step_data) > 2:
                for unexpanded_param in step_data[2:]:
                    expanded = unexpanded_param
                    for expansion_candidate in self._env_map:
                        expanded = expanded.replace(expansion_candidate, self._env_map[expansion_candidate])
                    step_params.append(expanded)

            if step_cmd in self._cmd_map.keys():
                self._driver.get_screenshot_as_file(self.mkfilename_screenshot(mode='A'))
                self._cmd_map[step_cmd](step_id, step_cmd, *step_params)
                self._driver.get_screenshot_as_file(self.mkfilename_screenshot(mode='B'))
            else:
                self.die_with_selenium("Unknown command [%s] - exiting" % step_cmd)


        self.orga()
        self.orga('* Logging')
        self.orga()
        self.orga('** Level INFO')
        self.orga()
        self.orga('#+INCLUDE: ../../log_INFO.txt src')
        self.orga()
        self.orga('** Level ERROR')
        self.orga()
        self.orga('#+INCLUDE: ../../log_ERROR.txt src')
        self.orga()

        logging.info("Generating HTML and ASCII reports...")
        subprocess.check_output("cd %s && %s 1>/dev/null 2>/dev/null; exit 0" % (os.path.join(self._odir, 'build', 'org'), 'emacs run.org --batch -f org-html-export-to-html --kill'), shell=True, universal_newlines=True)
        subprocess.check_output("cd %s && %s 1>/dev/null 2>/dev/null; exit 0" % (os.path.join(self._odir, 'build', 'org'), 'emacs run.org --batch -f org-ascii-export-to-ascii --kill'), shell=True, universal_newlines=True)
        logging.info("Generating HTML and ASCII reports... Done")


    def die_with_selenium(self, msg='unknown exit', exit_code=1):
        logging.error(msg)
        self.disconnect_selenium_remote()
        sys.exit(exit_code)


    def exec_get(self, id, cmd, url):
        logging.info("will run get on [%s]" % url)
        self._driver.get(url=url)


    def mkfilename_screenshot(self, mode):
        return os.path.join(self._odir, 'build', '_', 'screenshots', "screenshot%05d%s.png" % (self._step_index, mode))


    def orga(self, line=''):
        with open(self._orgfile, 'a') as f:
            f.write(line + '\n')


context = Context()
context.load()
context.connect_selenium_remote()
context.offyougo()
context.disconnect_selenium_remote()
