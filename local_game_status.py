import time
import logging as log
import re
from file_read_backwards import FileReadBackwards

from threading import Thread

import psutil as psutil
from definitions import UbisoftGame, GameType, GameStatus, ProcessType, WatchedProcess, SYSTEM, System

from steam import get_steam_game_status
from local_helper import get_local_game_path, get_game_installed_status



class ProcessWatcher(object):
    def __init__(self):
        self.watched_processes = []

    def watch_process(self, proces, game=None):
        try:
            process = WatchedProcess(
                process=proces,
                timeout=time.time() + 30,
                type=ProcessType.Game if game else ProcessType.Launcher,
                game=game if game else None,
            )
            self.watched_processes.append(process)
            return process
        except:
            return None

    def update_watched_processes_list(self):
        try:
            for proc in self.watched_processes:
                if not proc.process.is_running():
                    log.info(f"Removing {proc}")
                    self.watched_processes.remove(proc)
        except Exception as e:
            log.error(f"Error removing process from watched processes list {repr(e)}")


class GameStatusNotifier(object):
    def __init__(self, process_watcher):
        self.process_watcher = process_watcher
        self.games = {}
        self.watchers = {}
        self.statuses = {}
        self.launcher_log_path = None
        self._legacy_game_launched = False

        if SYSTEM == System.WINDOWS:
            Thread(target=self._process_data, daemon=True).start()

    def update_game(self, game: UbisoftGame):
        if game.install_id in self.watchers:
            if game.path == self.watchers[game.install_id].path:
                return

        self.games[game.install_id] = game

    def _is_process_alive(self, game):
        try:
            self.process_watcher.update_watched_processes_list()
            for process in self.process_watcher.watched_processes:
                if process.type == ProcessType.Game:
                    if process.game.install_id == game.install_id:
                        return True
            return False
        except Exception as e:
            log.error(f"Error checking if process is alive {repr(e)}")
            return False

    def _get_process_by_path(self, game: UbisoftGame):
        for p in psutil.process_iter(attrs=['exe'], ad_value=''):
            if game.path.lower() in p.info['exe'].lower():
                try:
                    if p.parent() and p.parent().exe() == game.path:
                        return p.parent().pid
                    return p.pid
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass

    def _handle_legacy_game_log(self, game):
        if self._legacy_game_launched:
            pid = self._get_process_by_path(game)
            if pid:
                self.process_watcher.watch_process(psutil.Process(int(pid)), game)
                self._legacy_game_launched = False
                return True
            else:
                return False
        else:
            # test if Legacy Game is still running
            return self._is_process_alive(game)

    def _read_log_data(self, game, log_line):
        if "disconnected" in log_line:
            return False
        if "has been started with product id" in log_line and f' {game.launch_id} (' in log_line:
            pid = int(re.search('Game with process id ([-+]?[0-9]+) has been started', log_line).group(1))
            if pid:
                self.process_watcher.watch_process(psutil.Process(pid), game)
                return True

        #  only when clicked PLAY on Legacy game
        if game.type == GameType.Legacy:
            if "Failed to fetch club game. Missing space id" in log_line:
                return self._handle_legacy_game_log(game)

    def _parse_log(self, game, line_list):
        if line_list:
            try:
                line = len(line_list) - 1
                while line > 0:
                    game_status = self._read_log_data(game, line_list[line])
                    if game_status is not None:
                        return game_status
                    line = line - 1
                return False

            except Exception as e:
                log.error(f"Error parsing launcher log file is game running {repr(e)}")
                return False
        else:
            return False

    def _is_game_running(self, game, line_list):
        try:
            if game.launch_id in self.statuses:
                if self.statuses[game.launch_id] == GameStatus.Running:
                    return self._is_process_alive(game)
                else:
                    return self._parse_log(game, line_list)
            else:
                return False
        except Exception as e:
            log.error(f"Error in checking is game running {line_list} {game.launch_id} / {repr(e)}")

    def _get_launcher_log_lines(self, number_of_lines):
        line_list = []
        if self.launcher_log_path:
            try:
                with FileReadBackwards(self.launcher_log_path, encoding="utf-8") as fh:
                    [line_list.append(fh.readline()) for _ in range(number_of_lines)]
            except FileNotFoundError:
                pass
            except UnicodeDecodeError:
                log.warning(
                    f"Can't read launcher log at {self.launcher_log_path}, UnicodeDecodeError when reading log lines")
            except Exception as e:
                log.warning(
                    f"Can't read launcher log at {self.launcher_log_path}, unable to read running games statuses: {repr(e)}")

        return line_list[::-1]

    def _get_game_status(self, game, line_list):
        status = None
        if game.type == GameType.Steam:
            status = get_steam_game_status(game.path)
        else:
            if not game.path:
                game.path = get_local_game_path(game.special_registry_path, game.launch_id)

            status = get_game_installed_status(game.path, game.exe, game.special_registry_path)
            if status == GameStatus.Installed:
                if self._is_game_running(game, line_list):
                    status = GameStatus.Running
        return status

    def _process_data(self):
        statuses = self.statuses
        while True:
            line_list = self._get_launcher_log_lines(20)
            if line_list:
                try:
                    for install_id, game in self.games.items():
                        statuses[install_id] = self._get_game_status(game, line_list)
                except Exception as e:
                    log.error(f"Process data error {repr(e)}")
                self.statuses = statuses

            time.sleep(1)

