from definitions import SYSTEM, System

from consts import UBISOFT_REGISTRY_LAUNCHER
import os
import logging as log

if SYSTEM == System.WINDOWS:
    import winreg
    import ctypes


class LocalClient(object):
    def __init__(self):
        self.last_modification_times = None
        self.configurations_path = None
        self.ownership_path = None
        self.settings_path = None
        self.launcher_log_path = None
        self.user_id = None
        self._is_installed = None
        self.refresh()

    def initialize(self, user_id):
        if not user_id:
            log.warning("Initialized with null user id!")
        log.info('Setting user id')
        self.user_id = user_id
        self.refresh()
        # Start tracking ownership file if exists
        self.ownership_changed()

    def ownership_accessible(self):
        if self.ownership_path is None:
            return False
        else:
            return os.access(self.ownership_path, os.R_OK)

    def settings_accessible(self):
        if self.settings_path is None:
            return False
        else:
            return os.access(self.settings_path, os.R_OK)

    def configurations_accessible(self):
        if self.configurations_path is None:
            return False
        else:
            return os.access(self.configurations_path, os.R_OK)

    def __read_file(self, filepath):
        try:
            with open(filepath, 'rb') as f:
                return f.read()
        except (FileExistsError, OSError, IOError) as e:
            log.warning(f'file not found [{e}]')
            return None

    def read_config(self):
        return self.__read_file(self.configurations_path)

    def read_ownership(self):
        return self.__read_file(self.ownership_path)

    def read_settings(self):
        return self.__read_file(self.settings_path)

    @property
    def is_installed(self):
        return self._is_installed

    def is_running(self):
        return ctypes.windll.user32.FindWindowW(None, "Uplay")

    @property
    def was_user_logged_in(self):
        if not self.ownership_path:
            return False
        return os.path.exists(self.ownership_path)

    def _find_windows_client(self):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, UBISOFT_REGISTRY_LAUNCHER, 0,
                                winreg.KEY_READ) as key:
                directory, _ = winreg.QueryValueEx(key, "InstallDir")
                return os.access(directory, os.F_OK), directory
        except OSError:
            return False, ''

    def refresh(self):
        if SYSTEM == System.MACOS:
            return

        exists, path = self._find_windows_client()
        if exists:
            if not self._is_installed:
                log.info('Local client installed')
                self._is_installed = True
            self.configurations_path = os.path.join(path, "cache", "configuration", "configurations")
            self.launcher_log_path = os.path.join(path, "logs", "launcher_log.txt")
            if self.user_id is not None:
                self.ownership_path = os.path.join(path, "cache", "ownership", self.user_id)
                self.settings_path = os.path.join(path, "cache", "settings", self.user_id)
        else:
            if self._is_installed:
                log.info('Local client uninstalled')
                self._is_installed = False
            self.configurations_path = None
            self.ownership_path = None
            self.settings_path = None
            self.launcher_log_path = None

    def ownership_changed(self):
        path = self.ownership_path
        try:
            stat = os.stat(path)
        except TypeError:
            log.warning('Undecided Ownership file path, uplay client might not be installed')
            self.refresh()
        except FileNotFoundError:
            log.warning(f'Ownership file at {path} path not present, user never logged in to uplay client.')
            self.refresh()
        except Exception as e:
            log.exception(f'Stating {path} has failed: {str(e)}')
            self.refresh()
        else:
            if stat.st_mtime != self.last_modification_times:
                self.last_modification_times = stat.st_mtime
                return True
        return False
