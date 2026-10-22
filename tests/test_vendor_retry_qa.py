"""QA checks retry behavior after *actual byte-stream* failure in the download function.

All network objects are deterministic in-memory fakes. Never contact vendors.
"""
from __future__ import annotations

import hashlib
import io

from desktop import components
from engine.control import Cancellation


def test_failed_stream_cleans_partial_and_second_attempt_is_verified(tmp_path, monkeypatch):
    payload = b"safe synthetic archive bytes" * 100
    pkg = components.Package("qa-retry", "https://developer.download.nvidia.com/qa-retry.zip",
                             hashlib.sha256(payload).hexdigest(), len(payload))
    attempts = []

    class Stream(io.BytesIO):
        def __init__(self, fail):
            super().__init__(payload)
            self.fail = fail
            self.reads = 0
        def read(self, size=-1):
            self.reads += 1
            if self.fail and self.reads == 2:
                raise TimeoutError("Injected network interruption")
            # Keep chunks short so the second read is exercised.
            return super().read(min(size, 200))

    class Opener:
        def open(self, *args, **kwargs):
            attempts.append(1)
            return Stream(len(attempts) == 1)

    monkeypatch.setattr(components, "build_opener", lambda *args: Opener())
    try:
        components.download(pkg, tmp_path, lambda _: None, Cancellation())
    except TimeoutError as err:
        assert "Injected network interruption" in str(err)
    else:
        raise AssertionError("The injected stream must fail")
    assert not list(tmp_path.iterdir()), "Neither partial nor unauthenticated ZIP may remain"

    archived = components.download(pkg, tmp_path, lambda _: None, Cancellation())
    assert archived.read_bytes() == payload
    assert len(attempts) == 2
    # A third attempt reuses the SHA-verified downloaded file; no network request.
    assert components.download(pkg, tmp_path, lambda _: None, Cancellation()) == archived
    assert len(attempts) == 2


def test_bad_cached_archive_is_not_accepted_without_reverification(tmp_path, monkeypatch):
    payload = b"verified bytes only"
    pkg = components.Package("qa-digest", "https://developer.download.nvidia.com/qa-digest.zip",
                             hashlib.sha256(payload).hexdigest(), len(payload))
    (tmp_path / "qa-digest.zip").write_bytes(b"x" * len(payload))
    calls = []
    class Opener:
        def open(self, *_args, **_kw):
            calls.append("download")
            return io.BytesIO(payload)
    monkeypatch.setattr(components, "build_opener", lambda *args: Opener())
    actual = components.download(pkg, tmp_path, lambda _: None, Cancellation())
    assert actual.read_bytes() == payload
    assert calls == ["download"]
