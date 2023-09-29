import os
import sys
import os.path
import logging
import json
import time
import traceback
import subprocess

from selenium.webdriver.firefox.options import Options as FFOptions
from selenium.webdriver.chrome.options import Options as CHOptions
from selenium import webdriver

from selenium.webdriver.common.keys import Keys as KEYS
from selenium.webdriver.common.by import By as BY

from selenium.webdriver.support.ui import WebDriverWait as WDW
from selenium.webdriver.support.ui import Select as SEL
from selenium.webdriver.support import expected_conditions as EC


def json_load_support_line_comments(filename):
    """Performs a return json.loads() from a file but leaves out // lines.
    """
    lines = []
    with open(filename, 'r') as f:
        lines = f.read().split("\n")
    lines_actual = []
    for line in lines:
        if not line.strip().startswith("//"):
            lines_actual.append(line)
    return json.loads("\n".join(lines_actual))


class Context:

    def __init__(self) -> None:
        self._valid_browsers = [ 'firefox', 'chrome' ]
        self._browser = os.getenv("OPENDCX_BROWSER", "firefox")
        if self._browser not in self._valid_browsers:
            self.die_very_early("unsupported browser requested [%s]" % self._browser)
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
        self._nofancy_map = {} # don't screenshot, DOM dump etc when it is an internal function
        self._cmd_map['get'] = self.exec_get
        
        self._cmd_map['stor_url'] = self.exec_stor_url
        self._nofancy_map['stor_url'] = True
        
        self._cmd_map['stor_env_load'] = self.exec_stor_env_load
        self._nofancy_map['stor_env_load'] = True

        self._cmd_map['sleep'] = self.exec_sleep

        self._cmd_map['refresh'] = self.exec_refresh
        
        self._cmd_map['press_return'] = self.exec_press_return
        
        self._step_index = 0
        self._orgfile = os.path.join(self._odir, 'build', 'org', 'run.org')


    def die_very_early(self, msg='unknown', exit_code=1):
        logging.error(msg)
        sys.exit(exit_code)


    def to_stor(self, k, v) -> None:
        filename = os.path.join(self._odir, 'build', '_', 'stor', '%s.txt' % k)
        with open(filename, 'w') as f:
            f.write(v)


    def append_stor(self, k, v) -> None:
        filename = os.path.join(self._odir, 'build', '_', 'stor', '%s.txt' % k)
        with open(filename, 'a') as f:
            f.write(v)


    def from_stor(self, k) -> str:
        filename = os.path.join(self._odir, 'build', '_', 'stor', '%s.txt' % k)
        with open(filename, 'r') as f:
            return f.read()


    def load(self) -> None:
        self._step_index = 0
        os.makedirs(self._odir, exist_ok=False)
        os.makedirs(os.path.join(self._odir, 'build', 'org'), exist_ok=False)
        os.makedirs(os.path.join(self._odir, 'build', '_', 'screenshots'), exist_ok=False)
        os.makedirs(os.path.join(self._odir, 'build', '_', 'stor'), exist_ok=False)
        os.makedirs(os.path.join(self._odir, 'downloads'), exist_ok=False)

        self.setup_logging()
        logging.debug(self._logfile_error)
        logging.debug("context loading...")
        if os.path.isfile(self._playbook):
            logging.debug("loading playbook")
            self._playbook_data = None
            try:
                self._playbook_data = json_load_support_line_comments(filename=self._playbook)
            except Exception as e:
                self.die_very_early(msg='JSON Playbook "%s" unparsable => %s' % (self._playbook.split('/')[-1], str(e)))
        else:
            logging.error("unable to find playbook")
            sys.exit(1)
        if os.path.isfile(self._playbookenv):
            logging.debug("loading playbook env")
            self._playbookenv_data = None
            try:
                self._playbookenv_data = json_load_support_line_comments(filename=self._playbookenv)
            except Exception as e:
                self.die_very_early(msg='JSON Playbook --ENV-- "%s" unparsable => %s' % (self._playbookenv.split('/')[-1], str(e)))

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
        self._choptions = CHOptions()

        self._driver: webdriver.Remote
        self._driver = None
        self._selenium_host = os.getenv("OPENDCX_SELENIUM_HOST", "host.docker.internal")
        self._selenium_port = os.getenv("OPENDCX_SELENIUM_PORT", "4444")
        try:
            if self._browser == "firefox":
                self._driver = webdriver.Remote(command_executor='http://%s:%s/wd/hub' % (self._selenium_host, self._selenium_port), options=self._ffoptions)
            if self._browser == "chrome":
                self._driver = webdriver.Remote(command_executor='http://%s:%s/wd/hub' % (self._selenium_host, self._selenium_port), options=self._choptions)
            logging.info("connected driver")
        except:
            logging.error("unable to connect driver")
            sys.exit(1)
        # maximize window size
        self._driver.maximize_window()

    def disconnect_selenium_remote(self) -> None:
        logging.info("will disconnect driver")
        self._driver.quit()


    def stepwalker(self):
        for s in self._playbook_data:
            yield s


    def offyougo(self):
        self.orga("* Comment/Description")
        self.orga()

        self.orga("#+begin_example")
        lines = ["N/A"]
        if os.path.isfile("/work/README"):
            with open("/work/README", 'r') as f:
                lines = f.read().strip().split("\n")
        for line in lines:
            self.orga(line)
        self.orga("#+end_example")

        self.orga()
        self.orga("""* Test run step by step""")
        self.orga()
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
                # pre exec status/A/in
                if not step_cmd in self._nofancy_map.keys():
                    self._driver.get_screenshot_as_file(self.mkfilename_screenshot(mode='A'))
                
                # execute step via command map and expand positional parameters
                self._cmd_map[step_cmd](step_id, step_cmd, *step_params)
                
                # post exec status/B/out
                if not step_cmd in self._nofancy_map.keys():
                    self._driver.get_screenshot_as_file(self.mkfilename_screenshot(mode='B'))
            else:
                self.die_with_selenium("Unknown command [%s] - exiting" % step_cmd)

        self.orga()

        debug_bytes = os.stat(self._logfile_debug).st_size
        info_bytes = os.stat(self._logfile_info).st_size
        error_bytes = os.stat(self._logfile_error).st_size

        self.orga("* Logging DEBUG/INFO/ERROR %d/%d/%d" % (debug_bytes, info_bytes, error_bytes))
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


    def exec_stor_url(self, id, cmd, k):
        self.to_stor(k, self._driver.current_url)


    def exec_stor_env_load(self, id, cmd, k):
        self._env_map['{{'+k+'}}'] = self.from_stor(k)


    def exec_sleep(self, id, cmd, seconds_str):
        time.sleep(float(seconds_str))

    def exec_refresh(self, id, cmd):
        self._driver.refresh()


    #todo
    def exec_press_return(self, id, cmd, msg=None):
        logging.info("Waiting for interactive PRESS RETURN by user...")
        if msg is not None:
            print(msg)
        print("Press RETURN to continue")
        input()
        logging.info("Waiting for interactive PRESS RETURN by user... USER PRESSED RETURN")


    #todo
    def exec_relget(self, id, cmd, urlpath):
        pass


    #todo
    def exec_stor_attribute(self, id, cmd, target_xpath, k):
        pass


    #todo
    def exec_stor_get_i(self, id, cmd, name, k):
        pass


    #todo
    def exec_clear_type(self, id, cmd, target_xpath, typing_content):
        pass

    #todo
    def exec_click(self, id, cmd, target_xpath):
        pass


    #todo
    def exec_click_text(self, id, cmd, target_xpath, txt):
        pass


    def mkfilename_screenshot(self, mode):
        return os.path.join(self._odir, 'build', '_', 'screenshots', "screenshot%05d%s.png" % (self._step_index, mode))


    def orga(self, line=''):
        """Append to ORG file (newline appended automatically).
        """
        with open(self._orgfile, 'a') as f:
            f.write(line + '\n')


context = Context()
context.load()
context.connect_selenium_remote()
context.offyougo()
context.disconnect_selenium_remote()
