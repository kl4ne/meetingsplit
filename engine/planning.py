"""Pure, deterministic partition planning. Core intervals cover [0,duration] exactly."""
from __future__ import annotations
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Clip:
    number: int
    core_start: float
    core_end: float
    export_start: float
    export_end: float

    def to_dict(self) -> dict:
        return asdict(self)


def choose_boundaries(duration: float, silence_ranges: list[tuple[float, float]],
                      target_seconds: float = 600.0, max_seconds: float = 840.0,
                      window_seconds: float = 75.0) -> list[float]:
    """Choose cuts near target, preferring long silence without exceeding max core length.

    A fallback cut still retains full signal thanks to export overlap. This is a
    practical safeguard, not a guarantee of semantic preservation.
    """
    if duration <= 0:
        raise ValueError("La duración debe ser positiva")
    if target_seconds < 30 or max_seconds < target_seconds:
        raise ValueError("Duración objetivo/máxima incorrecta")
    if window_seconds < 0:
        raise ValueError("Ventana negativa")
    cuts = [0.0]
    cursor = 0.0
    while duration - cursor > max_seconds:
        ideal = min(cursor + target_seconds, duration)
        left = max(cursor + 30.0, ideal - window_seconds)
        right = min(cursor + max_seconds, ideal + window_seconds)
        candidates: list[tuple[float, float]] = []
        for a, b in silence_ranges:
            if b - a < 0.2:
                continue
            t = min(max(ideal, a), b)
            if left <= t <= right:
                # Favor proximity to target, then natural silence duration.
                candidates.append((abs(ideal - t) - min(b-a, 2) * 0.2, t))
        nxt = min(candidates)[1] if candidates else min(ideal, cursor + max_seconds)
        if nxt <= cursor + 1:
            nxt = min(cursor + target_seconds, duration)
        cuts.append(round(nxt, 3))
        cursor = nxt
    cuts.append(round(duration, 3))
    return cuts


def plan_clips(duration: float, silences: list[tuple[float,float]],
               target_seconds: float=600.0, max_seconds: float=840.0,
               overlap_seconds: float=12.0) -> list[Clip]:
    if not 0 <= overlap_seconds <= 90:
        raise ValueError("Solapamiento fuera de rango")
    marks = choose_boundaries(duration, silences, target_seconds, max_seconds)
    clips: list[Clip] = []
    for n, (start, end) in enumerate(zip(marks, marks[1:]), 1):
        clips.append(Clip(n, start, end, max(0., start-overlap_seconds),
                          min(duration, end+overlap_seconds)))
    validate_clips(clips, duration, max_seconds, overlap_seconds)
    return clips


def validate_clips(clips: list[Clip], duration: float, max_seconds: float,
                   overlap_seconds: float) -> None:
    eps=0.01
    if not clips or abs(clips[0].core_start)>eps or abs(clips[-1].core_end-duration)>eps:
        raise ValueError("Cobertura incompleta")
    prev=0.
    for clip in clips:
        if abs(clip.core_start-prev)>eps:
            raise ValueError(f"Hueco o solapamiento de segmentos base en parte {clip.number}")
        if clip.core_end <= clip.core_start or clip.core_end-clip.core_start>max_seconds+eps:
            raise ValueError("Longitud base fuera de rango")
        if clip.export_start>clip.core_start or clip.export_end<clip.core_end:
            raise ValueError("El archivo no contiene el segmento base")
        if clip.core_start-clip.export_start>overlap_seconds+eps or clip.export_end-clip.core_end>overlap_seconds+eps:
            raise ValueError("Solapamiento fuera del máximo")
        prev=clip.core_end


def assign_text_to_core(start: float, end: float, core_start: float, core_end: float,
                        final: bool=False) -> bool:
    """Dedup by midpoint of timestamped word/segment; final core includes endpoint."""
    mid=(start+end)/2
    return core_start <= mid <= core_end if final else core_start <= mid < core_end
