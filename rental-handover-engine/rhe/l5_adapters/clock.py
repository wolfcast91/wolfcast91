"""L5 — Time, injected.

No logic anywhere else in this system may read a clock. Time enters through this
interface and nowhere else, which is what makes an eight-day overdue scenario
run in a millisecond and produce identical output every time.

All timestamps: UTC, ISO 8601, second precision, `Z` suffix. All duration maths:
integer seconds. There is no timezone handling because there are no timezones.
"""
from __future__ import annotations

import datetime as _dt
from typing import Protocol


class Clock(Protocol):
    def now_epoch(self) -> int: ...
    def now_utc(self) -> str: ...


def epoch_to_utc(epoch_seconds: int) -> str:
    if not isinstance(epoch_seconds, int):
        raise TypeError("epoch must be an integer number of seconds")
    return _dt.datetime.fromtimestamp(epoch_seconds, _dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_to_epoch(utc: str) -> int:
    return int(_dt.datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=_dt.timezone.utc).timestamp())


class FixedClock:
    """A clock that only moves when something explicitly moves it.

    Used in every test and every simulation. `advance` is the ONLY way time
    passes, so "the renter is four days late" is a line in a scenario file
    rather than a property of when you happened to run the suite.
    """

    def __init__(self, start_utc: str = "2026-03-01T08:00:00Z") -> None:
        self._epoch = utc_to_epoch(start_utc)
        self._start_epoch = self._epoch

    def now_epoch(self) -> int:
        return self._epoch

    def now_utc(self) -> str:
        return epoch_to_utc(self._epoch)

    def advance(self, seconds: int) -> "FixedClock":
        if not isinstance(seconds, int) or seconds < 0:
            raise ValueError("clock advances by a non-negative integer number of seconds")
        self._epoch += seconds
        return self

    def set_to(self, utc: str) -> "FixedClock":
        target = utc_to_epoch(utc)
        if target < self._epoch:
            raise ValueError(f"refusing to move the clock backwards: {self.now_utc()} -> {utc}")
        self._epoch = target
        return self

    def elapsed(self) -> int:
        return self._epoch - self._start_epoch


class SystemClock:
    """The real clock. Deliberately NOT used by any test, simulation, or golden
    comparison -- it exists only so the L5 seam is honest about what a production
    adapter would look like."""

    def now_epoch(self) -> int:
        return int(_dt.datetime.now(_dt.timezone.utc).timestamp())

    def now_utc(self) -> str:
        return epoch_to_utc(self.now_epoch())


DAY = 86400
HOUR = 3600
MINUTE = 60
