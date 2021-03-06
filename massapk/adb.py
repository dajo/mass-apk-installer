from typing import Union, NoReturn

import os
import functools
import subprocess
import logging
from enum import Enum, unique

from massapk import runtime_platform, pkg_root
from massapk.exceptions import MassApkError
from massapk.helpers import PLATFORM


log = logging.getLogger(__name__)


class AdbError(MassApkError):
    pass


class ApkAlreadyExists(AdbError):
    pass


class Adb(object):
    @unique
    class State(Enum):
        """Define adb-server state enum"""

        CONNECTED = True
        DISCONNECTED = False

    @unique
    class Flag(Enum):
        """Define adb-server package management
        supported flags for listing apks"""

        # fmt:off
        ALL = ""         # list all packages
        USER = "-3"      # list 3d party packages only (default)
        SYSTEM = "-S"    # list system packages only
        # fmt:on

    @classmethod
    def _get_adb_path(cls) -> os.path:
        """Return adb path based on operating system detected during import"""

        if runtime_platform == PLATFORM.OSX:

            return os.path.join(pkg_root, "bin", "osx", "adb")

        elif runtime_platform == PLATFORM.WIN:
            return os.path.join(pkg_root, "bin", "win", "adb.exe")

        elif runtime_platform == PLATFORM.LINUX:
            return os.path.join(pkg_root, "bin", "linux", "adb")

    def __init__(self, auto_connect=False):
        self._path = self._get_adb_path()
        self._state = self.__class__.State.DISCONNECTED
        if auto_connect:
            self.start_server()

    @property
    def path(self):
        """Get access to detected adb path"""
        return self._path

    @property
    def state(self) -> State:
        """
        Gets the state of adb server

        If `adb-server` state is `device` then phone is connected
        """
        return self._update_state()

    def _update_state(self) -> State:
        """Checks if an android phone is connected to adb-server via cable."""
        command_output = self._exec_command("get-state", return_stdout=True)

        if "error" not in command_output:
            log.warning("No phone connected waiting to connect phone")
            self._state = self.__class__.State.CONNECTED

        return self._state

    def start_server(self):
        """Starts adb-server process."""
        log.info("Starting adb server...")
        self._exec_command("start-server")

    def stop_server(self):
        """Kills adb server."""
        log.info("Killing adb server...")
        self._exec_command("kill-server")

    def _exec_command(
        self, cmd, return_stdout=False, case_sensitive=False
    ) -> Union[NoReturn, str]:
        """Low level function to send shell commands to running adb-server process.

        :raises AdbError
        """

        cmd = f"{self._path} {cmd}"
        return_code, output = subprocess.getstatusoutput(cmd)

        if return_code:
            if output:
                raise AdbError(output)

            log.warning(f"command returned error code {return_code}, but no output")

        if return_stdout:
            return output.lower() if not case_sensitive else output

    def push(self, source_path, ignore_errors=True):
        """Pushes apk package to android device.

        Before calling `push` function make sure function `connect` has been
        called earlier and `self.state` value is set to `connected`

        extra parameters are passed to adb-server in order to  avoid errors like the following
        faulty error messages:
            `operation failed apk is already installed on the device`
            `operation failed apk version is lower than the one currently installed on the device`

         -d is to allow down grade of apk
         -r is to reinstall existing apk
         """

        try:
            self._exec_command(f"install -d -r {source_path}")
        except AdbError as error:
            log.warning(repr(error))
            if not ignore_errors:
                raise error from None

    def pull(self, apk_path: str):
        """Pull's an apk from the following path in the android device."""
        self._exec_command(cmd=f" pull {apk_path}")

    def list_device(self, flag: Flag):
        """Lists installed apk  packages on the android device.

        Results can be filtered with PKG_FILTER to get only apk packages
        you are interested. Defaults to list 3d party apps.


        list packages [-f] [-d] [-e] [-s] [-3] [-i] [-l] [-u] [-U]
              [--show-versioncode] [--apex-only] [--uid UID] [--user USER_ID] [FILTER]
            Prints all packages; optionally only those whose name contains
            the text in FILTER.  Options are:
              -f: see their associated file
              -a: all known packages (but excluding APEXes)
              -d: filter to only show disabled packages
              -e: filter to only show enabled packages
              -s: filter to only show system packages
              -3: filter to only show third party packages
              -i: see the installer for the packages
              -l: ignored (used for compatibility with older releases)
              -U: also show the package UID
              -u: also include uninstalled packages
              --show-versioncode: also show the version code
              --apex-only: only show APEX packages
              --uid UID: filter to only show packages with the given UID
              --user USER_ID: only list packages belonging to the given user

        """

        log.info("Listing installed apk's in the device ...")
        output = self._exec_command(
            f"shell pm list packages {flag.value}",
            return_stdout=True,
            case_sensitive=True,
        )

        # adb returns packages name in the form
        # package:com.skype.raider
        # we need to strip "package:" prefix
        return [
            line.split(":", maxsplit=1)[1].strip()
            for line in output.splitlines()
            if line.startswith("package:")
        ]
