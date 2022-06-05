import base64
import json
import os
import sys
import time
import unittest
from datetime import datetime
from pathlib import Path
from appium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import logging

def defaultConfig(config_file=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if config_file is not None:
                kwargs["config_file"] = config_file
            kwargs["tc_path"] = Path(func.__globals__["__file__"])
            func(*args, **kwargs)

        return wrapper

    return decorator

class Testcase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        self.tc_path = kwargs.get("tc_path")
        self.config_file = kwargs.get("config_file")
        kwargs = {}
        super().__init__(*args, **kwargs)
        self.platform = None
        self.custom_json = None

        print(self.tc_path)

    def _checkValue(self, arg):
        if type(arg) == str:
            if arg is None or len(arg) == 0:
                raise ValueError from None
        elif type(arg) == dict:
            if arg is None or len(arg.items()) == 0:
                raise ValueError from None
        else:
            if arg is None:
                raise ValueError from None

    def getJsonProperties(self, project_root: str, custom_json: str) -> json:
        try:
            self._checkValue(custom_json)
        except Exception as e:
            raise e

        json_path = os.path.join(project_root, custom_json)

        try:
            with open(json_path, "r") as json_file:
                json_data = json.load(json_file)
            print(json_data)
        except FileNotFoundError:
            errorMsg = "json properties(self.custom_json) is not found. %s" % json_path
            print(errorMsg)
            raise FileNotFoundError(errorMsg)
        except Exception as e:
            errorMsg = "json properties(self.custom_json) happen exception. %s" % json_path
            print(errorMsg)
            print(e)
            raise e

        if json_data is None or len(json_data.keys()) == 0:
            errorMsg = "json properties(self.custom_json) is not loaded. Please check json file."
            print(errorMsg)
            raise Exception(errorMsg)

        return json_data

    def setWebDriver(self, WEBDRIVER_DIR: str, platform_json: json) -> (WebDriver, WebDriverWait):
        try:
            self._checkValue(WEBDRIVER_DIR)
        except Exception as e:
            raise e
        options = None

        if platform_json.get("headless") is not None:
            if platform_json["headless"] == "Y":
                options = ChromeOptions()
                options.add_argument("headless")
                options.add_argument("windows-size=1280x764")
                options.add_argument("disable-gpu")
                driver = WebDriver(executable_path=WEBDRIVER_DIR, chrome_options=options)
            elif platform_json["headless"] == "N":
                driver = WebDriver(executable_path=WEBDRIVER_DIR)
            else:
                errorMsg = (
                    "headless mode just use Y or N. But argument is %s. Please change json property."
                    % platform_json["headless"]
                )
                print(errorMsg)
                raise Exception(errorMsg)

        if platform_json.get("remote") is not None:
            if platform_json["remote"] == "Y":
                host = platform_json["remote"].get("host")
                port = platform_json["remote"].get("port")

                options = ChromeOptions()
                options.add_argument("headless")
                options.add_argument("windows-size=1280x764")
                options.add_argument("disable-gpu")

                self.driver = webdriver.Remote(
                    command_executor=f"{host}:{port}/wd/hub", desired_capabilities=options.to_capabilities()
                )
                print("## Remote Selenium Mode - headless ##")
            else:
                print("## Local Selenium Mode ##")
        else:
            if options is not None:
                driver = WebDriver(executable_path=WEBDRIVER_DIR, chrome_options=options)
            else:
                driver = WebDriver(executable_path=WEBDRIVER_DIR)
        if platform_json.get("download_path") is not None:
            params = {"behavior": "allow", "downloadPath": platform_json["download_path"]}
            driver.execute_cdp_cmd("Page.setDownloadBehavior", params)

        if platform_json.get("recording_screen") is not None:
            if platform_json["recording_screen"] == "Y":
                # jar loader : https://jpype.readthedocs.io/en/latest/userguide.html
                # load TestRecorder jar
                # jpype.startJVM(classpath=['tests/resource/jar/ATUTestRecorder_2.1.jar'])
                # # dynamic import module
                # from atu.testrecorder import ATUTestRecorder
                # # make instance
                # self.web_recorder = ATUTestRecorder("./logs", False)
                # # start record
                # self.web_recorder.start()
                # # stop record
                # self.web_recorder.stop()
                print("## Enable web recorder ##")
            else:
                print("## Disable web recorder ##")

        driver.implicitly_wait(time_to_wait=5)
        # browser size max
        driver.maximize_window()
        wait = WebDriverWait(driver, 10)

        return driver, wait

    def setUp(self):
        self.filemgr = FileManage()
        WEBDRIVER_DIR = os.path.join(self.filemgr.resource_path, "driver", "chromedriver")
        project_root = self.filemgr.project_root

        if self.custom_json is None and self.tc_path is not None:
            _path = os.path.relpath(self.tc_path, project_root)
            _arr_path = _path.split("/")
            if self.config_file is None:
                self.config_file = "common.json"

            default_json_path = os.path.join(
                project_root, _arr_path[0], _arr_path[1], "resource", "config", self.config_file
            )
            if os.path.exists(default_json_path):
                self.custom_json = os.path.join(_arr_path[0], _arr_path[1], "resource", "config", self.config_file)
                print(f"set default property json file. {default_json_path}")

        if self.platform == "web":
            self.json_properties = self.getJsonProperties(project_root, self.custom_json)
            self.driver, self.wait = self.setWebDriver(WEBDRIVER_DIR, self.json_properties["drivers"][0])
        else:
            raise Exception("platform type is not defined.")

    def tearDown(self):
        self.driver.quit()


class CustomCall:
    def __iter__(self):
        self.a = 1
        return self

    def __next__(self):
        k = self.a
        self.a += 1
        return k
