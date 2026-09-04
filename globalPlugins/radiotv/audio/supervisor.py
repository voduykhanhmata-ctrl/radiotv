# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

"""Latest-request-wins process supervisor for the isolated playback worker."""

from __future__ import annotations

import json
import logging
import os
import pathlib
import struct
import subprocess
import threading
import time
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from .messages import ProtocolError, parse_engine_message
from ..core.entities import DEFAULT_HTTP_USER_AGENT, is_safe_http_url


@dataclass(frozen=True, slots=True)
class PlaybackEvent:
    request_id: str
    state: str
    detail: str = ""
    replay_count: int = 0


@dataclass(slots=True)
class _Session:
    request_id: str
    url: str
    volume: int
    user_agent: str
    process: subprocess.Popen[str] | None = None
    confirmed: bool = False
    active: bool = False
    stop_requested: bool = False
    normal_end: bool = False
    error_reported: bool = False
    replay_count: int = 0
    startup_timer: threading.Timer | None = field(default=None, repr=False)


CommandBuilder = Callable[[str, str, int, pathlib.Path], Sequence[str]]
EventCallback = Callable[[PlaybackEvent], None]


class PlaybackSupervisor:
    """Own at most one worker, cancel old requests, and replay one confirmed crash."""

    def __init__(
        self,
        *,
        worker_script: str | pathlib.Path | None = None,
        runtime_root: str | pathlib.Path | None = None,
        on_event: EventCallback | None = None,
        startup_timeout: float = 60.0,
        stop_grace: float = 1.0,
        command_builder: CommandBuilder | None = None,
        logger: logging.Logger | None = None,
    ):
        audio_directory = pathlib.Path(__file__).resolve().parent
        self._worker_script = pathlib.Path(
            worker_script or audio_directory / "engine_process.ps1"
        )
        self._runtime_root = pathlib.Path(
            runtime_root or audio_directory.parent / "runtime"
        )
        self._on_event = on_event
        self._startup_timeout = startup_timeout
        self._stop_grace = stop_grace
        self._command_builder = command_builder or self._build_default_command
        self._lock = threading.RLock()
        self._current: _Session | None = None
        self._monitor_threads: set[threading.Thread] = set()
        self._closed = False
        self._logger = logger

    @property
    def current_request_id(self) -> str | None:
        with self._lock:
            return self._current.request_id if self._current else None

    @property
    def is_playing(self) -> bool:
        with self._lock:
            return bool(self._current and self._current.active)

    def set_event_callback(self, callback: EventCallback | None) -> None:
        with self._lock:
            self._on_event = callback

    def play(
        self,
        url: str,
        volume: int,
        user_agent: str = DEFAULT_HTTP_USER_AGENT,
        *,
        request_id: str | None = None,
    ) -> str:
        self._validate_request(url, volume, user_agent)
        request_id = request_id or str(uuid.uuid4())
        session = _Session(
            request_id=request_id,
            url=url,
            volume=volume,
            user_agent=user_agent,
        )
        with self._lock:
            if self._closed:
                raise RuntimeError("playback supervisor is closed")
            previous = self._current
            self._current = session
        if previous is not None:
            previous.stop_requested = True
            self._cancel_timer(previous)
            self._terminate_process(previous)
        self._emit(session, "starting")
        self._launch_in_background(session)
        return request_id

    def stop(self) -> None:
        with self._lock:
            session = self._current
            self._current = None
        if session is None:
            return
        session.stop_requested = True
        self._cancel_timer(session)
        self._terminate_process(session)
        self._emit(session, "stopped")

    def set_volume(self, volume: int, *, request_id: str | None = None) -> str | None:
        if type(volume) is not int or not 0 <= volume <= 100:
            raise ValueError("volume must be an integer from 0 to 100")
        with self._lock:
            session = self._current
            if session is None:
                return None
            url = session.url
            user_agent = session.user_agent
        return self.play(url, volume, user_agent, request_id=request_id)

    def shutdown(self) -> None:
        with self._lock:
            self._closed = True
        self.stop()
        with self._lock:
            monitors = tuple(self._monitor_threads)
        deadline = time.monotonic() + self._stop_grace + 1.0
        for monitor in monitors:
            if monitor is not threading.current_thread():
                monitor.join(timeout=max(0.0, deadline - time.monotonic()))

    def _launch_in_background(self, session: _Session) -> None:
        def run() -> None:
            try:
                self._launch(session)
            finally:
                with self._lock:
                    self._monitor_threads.discard(threading.current_thread())

        worker = threading.Thread(target=run, name="RadioTVEngineLaunch", daemon=True)
        with self._lock:
            if self._closed or self._current is not session or session.stop_requested:
                return
            self._monitor_threads.add(worker)
            worker.start()

    @staticmethod
    def _dispose_unmonitored_process(process: subprocess.Popen[str]) -> None:
        try:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=2.0)
        except (OSError, subprocess.TimeoutExpired):
            pass
        finally:
            for pipe in (process.stdin, process.stdout):
                if pipe is not None:
                    try:
                        pipe.close()
                    except OSError:
                        pass

    def _launch(self, session: _Session) -> None:
        runtime_directory = self._runtime_root / (
            "x64" if struct.calcsize("P") == 8 else "x86"
        )
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        process = None
        try:
            command = list(self._command_builder(
                session.request_id, session.url, session.volume, runtime_directory,
            ))
            with self._lock:
                if self._current is not session or session.stop_requested:
                    return
            process = subprocess.Popen(
                command,
                cwd=str(self._worker_script.parent),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=creation_flags,
            )
            start_command = {
                "version": 1,
                "requestId": session.request_id,
                "url": session.url,
                "volume": session.volume,
                "userAgent": session.user_agent,
            }
            assert process.stdin is not None
            process.stdin.write(json.dumps(start_command, ensure_ascii=False) + "\n")
            process.stdin.flush()
            process.stdin.close()
        except (OSError, ValueError, RuntimeError) as error:
            if process is not None:
                self._dispose_unmonitored_process(process)
            self._fail_launch(session, f"worker launch failed: {type(error).__name__}")
            return

        with self._lock:
            abandoned = self._current is not session or session.stop_requested
            if not abandoned:
                session.process = process
                session.confirmed = False
                session.active = False
                session.normal_end = False
                session.error_reported = False
                timer = threading.Timer(
                    self._startup_timeout,
                    self._handle_startup_timeout,
                    args=(session, process),
                )
                timer.daemon = True
                session.startup_timer = timer
                timer.start()
        if abandoned:
            self._dispose_unmonitored_process(process)
            return
        monitor = threading.Thread(
            target=self._monitor,
            args=(session, process),
            name=f"RadioTVEngine-{session.request_id[:8]}",
            daemon=True,
        )
        with self._lock:
            self._monitor_threads.add(monitor)
        monitor.start()

    def _monitor(self, session: _Session, process: subprocess.Popen[str]) -> None:
        assert process.stdout is not None
        try:
            for line in iter(lambda: process.stdout.readline(4097), ""):
                if not self._is_current(session, process):
                    break
                if not line.strip():
                    continue
                try:
                    message = parse_engine_message(line, session.request_id)
                except ProtocolError as error:
                    session.error_reported = True
                    self._cancel_timer(session)
                    self._clear_if_current(session)
                    self._emit(session, "error", f"protocol: {error}")
                    self._terminate_process(session)
                    break
                if not self._is_current(session, process):
                    break
                if message.message_type == "ready":
                    self._emit(session, "ready", replay_count=session.replay_count)
                elif message.message_type == "error":
                    session.error_reported = True
                    self._cancel_timer(session)
                    self._clear_if_current(session)
                    detail = message.code or "engine_error"
                    if message.detail:
                        detail = f"{detail}: {message.detail}"
                    self._emit(session, "error", detail)
                    self._terminate_process(session)
                    break
                elif message.state == "playing":
                    with self._lock:
                        if not self._is_current(session, process):
                            break
                        session.confirmed = True
                        session.active = True
                        self._cancel_timer(session)
                    self._emit(
                        session,
                        "playing",
                        replay_count=session.replay_count,
                    )
                elif message.state == "stalled":
                    session.active = False
                    self._emit(session, "stalled", replay_count=session.replay_count)
                elif message.state == "ended":
                    session.normal_end = True
                    self._cancel_timer(session)
                    self._clear_if_current(session)
                    self._emit(session, "ended", replay_count=session.replay_count)
                    self._terminate_process(session)
                    break
        finally:
            return_code: int | None = None
            try:
                return_code = process.wait(timeout=self._stop_grace + 0.5)
            except subprocess.TimeoutExpired:
                pass
            finally:
                try:
                    process.stdout.close()
                except OSError:
                    pass
                with self._lock:
                    self._monitor_threads.discard(threading.current_thread())
            if return_code is not None:
                self._handle_exit(session, process, return_code)

    def _handle_exit(
        self,
        session: _Session,
        process: subprocess.Popen[str],
        return_code: int,
    ) -> None:
        if not self._is_current(session, process):
            return
        self._cancel_timer(session)
        if session.stop_requested or session.normal_end or session.error_reported:
            self._clear_if_current(session)
            return
        if session.confirmed and session.replay_count < 1:
            session.replay_count += 1
            self._emit(session, "restarting", replay_count=session.replay_count)
            self._launch_in_background(session)
            return
        self._clear_if_current(session)
        self._emit(session, "error", f"engine exited ({return_code})")

    def _handle_startup_timeout(
        self, session: _Session, process: subprocess.Popen[str]
    ) -> None:
        with self._lock:
            if not self._is_current(session, process) or session.confirmed:
                return
            session.error_reported = True
            self._clear_if_current(session)
        self._emit(session, "error", "startup timeout")
        self._terminate_process(session)

    def _fail_launch(self, session: _Session, detail: str) -> None:
        with self._lock:
            if self._current is not session or session.stop_requested:
                return
            session.error_reported = True
            self._clear_if_current(session)
        self._emit(session, "error", detail)

    def _terminate_process(self, session: _Session) -> None:
        process = session.process
        if process is None or process.poll() is not None:
            return
        try:
            process.terminate()
        except OSError:
            return
        reaper = threading.Thread(
            target=self._kill_after_grace,
            args=(process,),
            name="RadioTVEngineStop",
            daemon=True,
        )
        reaper.start()

    def _kill_after_grace(self, process: subprocess.Popen[str]) -> None:
        try:
            process.wait(timeout=self._stop_grace)
        except subprocess.TimeoutExpired:
            try:
                process.kill()
                process.wait(timeout=self._stop_grace)
            except (OSError, subprocess.TimeoutExpired):
                pass

    def _cancel_timer(self, session: _Session) -> None:
        timer = session.startup_timer
        session.startup_timer = None
        if timer is not None:
            timer.cancel()

    def _is_current(
        self, session: _Session, process: subprocess.Popen[str]
    ) -> bool:
        with self._lock:
            return self._current is session and session.process is process

    def _clear_if_current(self, session: _Session) -> None:
        with self._lock:
            if self._current is session:
                self._current = None

    def _emit(
        self,
        session: _Session,
        state: str,
        detail: str = "",
        *,
        replay_count: int | None = None,
    ) -> None:
        if self._logger is not None:
            # Never log URL, command, user-agent, or free-form worker details.
            self._logger.info("playback state=%s replay=%d", state, session.replay_count)
        callback = self._on_event
        if callback is None:
            return
        event = PlaybackEvent(
            request_id=session.request_id,
            state=state,
            detail=detail,
            replay_count=session.replay_count if replay_count is None else replay_count,
        )
        try:
            callback(event)
        except Exception:
            pass

    def _build_default_command(
        self,
        request_id: str,
        _url: str,
        _volume: int,
        runtime_directory: pathlib.Path,
    ) -> Sequence[str]:
        windows_directory = os.environ.get("SystemRoot", r"C:\Windows")
        powershell = pathlib.Path(
            windows_directory,
            "System32",
            "WindowsPowerShell",
            "v1.0",
            "powershell.exe",
        )
        return (
            str(powershell),
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(self._worker_script),
            "-RuntimeDir",
            str(runtime_directory),
            "-RequestId",
            request_id,
        )

    @staticmethod
    def _validate_request(url: str, volume: int, user_agent: str) -> None:
        if not is_safe_http_url(url):
            raise ValueError("url must be a safe HTTP(S) URL")
        if type(volume) is not int or not 0 <= volume <= 100:
            raise ValueError("volume must be an integer from 0 to 100")
        if (
            not isinstance(user_agent, str)
            or not user_agent
            or len(user_agent) > 256
            or "\r" in user_agent
            or "\n" in user_agent
            or any(
                ord(character) < 32 or ord(character) == 127
                for character in user_agent
            )
        ):
            raise ValueError("user_agent must be a safe HTTP header value")
