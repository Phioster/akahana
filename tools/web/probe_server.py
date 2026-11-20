"""Serves the web export and collects what tools/web/probe.js sends: one JSON line per message in
<logs>/<device>.jsonl. Usage: python3 probe_server.py <web dir> <logs dir> [port]"""
import http.server
import json
import os
import sys
import functools

TYPES = {'.wasm': 'application/wasm', '.pck': 'application/octet-stream', '.js': 'text/javascript'}


class Handler(http.server.SimpleHTTPRequestHandler):
    logs = '.'

    def guess_type(self, path):
        return TYPES.get(os.path.splitext(path)[1], super().guess_type(path))

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def do_POST(self):
        if self.path != '/log':
            self.send_error(404)
            return
        body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        try:
            msg = json.loads(body)
        except ValueError:
            msg = {'type': 'kaputt', 'msg': body[:500].decode('utf-8', 'replace')}
        dev = ''.join(c for c in str(msg.get('dev', 'unbekannt')) if c.isalnum() or c in '-_') or 'unbekannt'
        with open(os.path.join(self.logs, dev + '.jsonl'), 'a', encoding='utf-8') as f:
            f.write(json.dumps(msg, ensure_ascii=False) + '\n')
        self.send_response(204)
        self.end_headers()

    def log_message(self, *a):
        pass


def main():
    web, logs = sys.argv[1], sys.argv[2]
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 8000
    os.makedirs(logs, exist_ok=True)
    Handler.logs = os.path.abspath(logs)
    http.server.ThreadingHTTPServer(('0.0.0.0', port), functools.partial(Handler, directory=web)).serve_forever()


if __name__ == '__main__':
    main()
