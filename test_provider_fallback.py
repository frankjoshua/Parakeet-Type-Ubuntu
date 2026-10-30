"""Self-check: a GPU provider that can't load falls back to CPU, loudly.

With provider "cuda", a missing CUDA/cuDNN library makes sherpa-onnx raise
RuntimeError at recognizer build. Dictation must keep working on CPU and say
why in the history log, not die on the first hotkey press.

Run with the app venv: .venv/bin/python3 test_provider_fallback.py
Pure logic — no display, audio, GPU, or model files needed.
"""
import sys
import tempfile
from pathlib import Path

import dictation_app as da


def main():
    tmp = Path(tempfile.mkdtemp())
    da.DATA_DIR = tmp
    da.HISTORY_FILE = tmp / "history.log"
    da.ASREngine._warm = lambda self: None

    tried = []

    def build(self, provider):
        tried.append(provider)
        if provider != "cpu":
            raise RuntimeError("Failed to load shared library")
        return "cpu-recognizer"

    da.ASREngine._build_offline_recognizer = build
    noop = lambda *a: None
    profile = da.load_model_profiles()["profiles"]["desktop"]

    engine = da.ASREngine(da.AppConfig(provider="cuda"), profile, noop, noop, noop)
    assert engine._get_recognizer() == "cpu-recognizer", "no cpu fallback"
    assert tried == ["cuda", "cpu"], tried
    assert "provider 'cuda' unavailable" in da.HISTORY_FILE.read_text(), "fallback not logged"

    # A CPU build failure is a real error, not something to retry
    engine = da.ASREngine(da.AppConfig(provider="cpu"), profile, noop, noop, noop)
    da.ASREngine._build_offline_recognizer = lambda self, p: (_ for _ in ()).throw(RuntimeError("boom"))
    try:
        engine._get_recognizer()
    except RuntimeError:
        pass
    else:
        raise AssertionError("cpu build failure swallowed")

    print("OK: unavailable GPU provider falls back to cpu and logs it")


if __name__ == "__main__":
    sys.exit(main())
