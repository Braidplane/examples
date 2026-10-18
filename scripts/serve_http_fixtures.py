"""Serve only the two canonical synthetic HTTP fixtures; no directory browsing."""
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'recipes'
FIXTURES = {
    '/orders': ('http-customer-enrichment/fixtures/orders.json', 'application/json'),
    '/receipt.bin': ('opaque-file-archive/fixtures/receipt.bin', 'application/octet-stream'),
}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            data, kind = b'{}', 'application/json'
        elif self.path in FIXTURES:
            name, kind = FIXTURES[self.path]
            data = (ROOT / name).read_bytes()
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bind', default='127.0.0.1')
    parser.add_argument('--port', type=int, required=True, help='Available local port; 0 selects an ephemeral port')
    args = parser.parse_args()
    with HTTPServer((args.bind, args.port), Handler) as server:
        print(f'Fixture server listening on {args.bind}:{server.server_port}', flush=True)
        server.serve_forever()
