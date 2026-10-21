"""Cooperative cancellation for long local audio jobs."""
from __future__ import annotations
import threading

class JobCancelled(RuntimeError):
    """The user requested cancellation, not an unexpected error."""

class Cancellation:
    def __init__(self):
        self.event = threading.Event()
    def cancel(self):
        self.event.set()
    def check(self):
        if self.event.is_set():
            raise JobCancelled('Cancelado por el usuario; los archivos completados se conservaron.')
