#!/usr/bin/env python3
"""Dev server: index.html を localhost でホストする(キャッシュ無効)。

使い方:
    python3 serve.py          # http://127.0.0.1:9292
    python3 serve.py 3000     # ポート指定
"""
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # 開発用: リロードで常に最新の index.html が読まれるように
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Expires", "0")
        super().end_headers()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9292
    root = Path(__file__).resolve().parent
    handler = lambda *a, **kw: NoCacheHandler(*a, directory=str(root), **kw)
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"Serving {root} at http://127.0.0.1:{port}/ (Ctrl+C で終了)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
