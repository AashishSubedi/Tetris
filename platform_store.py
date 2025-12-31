# platform_store.py
import sys
import json
from pathlib import Path

IS_WEB = (sys.platform == "emscripten")
HIGH_SCORE_PATH = Path(__file__).with_name("highscore.json")


def load_high_score() -> int:
    # Web (pygbag): localStorage
    if IS_WEB:
        try:
            import js  # provided by pygbag
            v = js.window.localStorage.getItem("tetris_high_score")
            return int(v) if v is not None else 0
        except Exception:
            return 0

    # Desktop: file
    try:
        data = json.loads(HIGH_SCORE_PATH.read_text(encoding="utf-8"))
        return int(data.get("high_score", 0))
    except Exception:
        return 0


def save_high_score(score: int) -> None:
    score = int(score)

    # Web (pygbag): localStorage
    if IS_WEB:
        try:
            import js
            js.window.localStorage.setItem("tetris_high_score", str(score))
        except Exception:
            pass
        return

    # Desktop: file
    try:
        HIGH_SCORE_PATH.write_text(json.dumps({"high_score": score}, indent=2), encoding="utf-8")
    except Exception:
        pass
