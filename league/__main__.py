"""Entry point for ``python3 -m league``.

Forces UTF-8 on stdin/stdout and ``\\n`` line endings on stdout so behaviour is
identical on macOS, Linux and Windows, then delegates to the CLI.
"""

from __future__ import annotations

import sys

from league.cli import main


def _force_utf8_streams() -> None:
    # Real stdio streams are reconfigurable; a redirected or wrapped stream may not be.
    for stream, kwargs in (
        (sys.stdin, {"encoding": "utf-8"}),
        (sys.stdout, {"encoding": "utf-8", "newline": "\n"}),
    ):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(**kwargs)


if __name__ == "__main__":
    _force_utf8_streams()
    raise SystemExit(main())
