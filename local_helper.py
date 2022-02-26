from definitions import SYSTEM, System, GameStatus

import os
import asyncio
import logging as log
from consts import UBISOFT_REGISTRY_LAUNCHER_INSTALLS

if SYSTEM == System.WINDOWS:
    import winreg


def _get_registry_value_from_path(top_key, registry_path, key):
    with winreg.OpenKey(top_key, registry_path, 0, winreg.KEY_READ) as winkey:
        return winreg.QueryValueEx(winkey, key)[0]


def _return_local_game_path_from_special_registry(special_registry_path):
    if not special_registry_path:
        return GameStatus.NotInstalled
    try:
        install_location = _get_registry_value_from_path(winreg.HKEY_LOCAL_MACHINE, special_registry_path,
                                                         "InstallLocation")
        return install_location
    except WindowsError:
        # Entry doesn't exist, game is not installed.
        return ""
    except Exception as e:
        log.warning(f"Unable to read special registry status for {special_registry_path}: {repr(e)}")
        return ""


def _return_local_game_path(launch_id):
    installs_path = UBISOFT_REGISTRY_LAUNCHER_INSTALLS
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, installs_path):
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, installs_path + f'\\{launch_id}') as lkey:
                    game_path, _ = winreg.QueryValueEx(lkey, 'InstallDir')
                    return os.path.normcase(os.path.normpath(game_path))
            except OSError:
                return ""  # end of iteration
    except WindowsError:
        return ""  # Game not installed / during installation


def get_local_game_path(special_registry_path, launch_id):
    local_game_path = _return_local_game_path(launch_id)
    if not local_game_path and special_registry_path:
        local_game_path = _return_local_game_path_from_special_registry(special_registry_path)
    return local_game_path


async def get_size_at_path(start_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
                await asyncio.sleep(0)

    return total_size

def _is_file_at_path(path, file):
    if os.path.isdir(path):
        file_location = os.path.join(path, file)
        if os.path.isfile(file_location):
            return True
        return False
    else:
        return False


def _read_status_from_state_file(game_path):
    try:
        if os.path.exists(os.path.join(game_path, 'uplay_install.state')):
            with open(os.path.join(game_path, 'uplay_install.state'), 'rb') as f:
                if f.read()[0] == 0x0A:
                    return GameStatus.Installed
                else:
                    return GameStatus.NotInstalled
        # State file doesn't exit
        else:
            return GameStatus.NotInstalled
    except Exception as e:
        log.warning(f"Issue reading install state file for {game_path}: {repr(e)}")
        return GameStatus.NotInstalled


def get_game_installed_status(path, exe=None, special_registry_path=None):
    status = GameStatus.NotInstalled
    try:
        if path and os.access(path, os.F_OK):
            status = _read_status_from_state_file(path)
            # Fallback for old games
            if status == GameStatus.NotInstalled and exe and special_registry_path:
                if _is_file_at_path(path, exe):
                    status = GameStatus.Installed
    except Exception as e:
        log.error(f"Error reading game installed status at {path}: {repr(e)}")
    finally:
        return status