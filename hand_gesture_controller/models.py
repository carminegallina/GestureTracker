from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class LandmarkPoint:
    x: float
    y: float
    z: float = 0.0


@dataclass(frozen=True)
class HandResult:
    landmarks: List[LandmarkPoint]
    handedness: str
    raw_landmarks: object
    is_tracked: bool = True
