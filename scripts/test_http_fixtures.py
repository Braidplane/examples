from http.server import HTTPServer
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

from serve_http_fixtures import FIXTURES, Handler, ROOT


class HTTPFixtureTests(unittest.TestCase):
    def test_canonical_bytes_types_health_and_no_other_files(self):
        with HTTPServer(('127.0.0.1', 0), Handler) as server:
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            try:
                base = f'http://127.0.0.1:{server.server_port}'
                for route, (name, kind) in FIXTURES.items():
                    with urlopen(base + route, timeout=5) as response:
                        self.assertEqual(response.headers['Content-Type'], kind)
                        self.assertEqual(response.read(), (ROOT / name).read_bytes())
                with urlopen(base + '/health', timeout=5) as response:
                    self.assertEqual(response.status, 200)
                for route in ('/', '/../../.git/config', '/fixtures/orders.json'):
                    with self.assertRaises(HTTPError) as caught:
                        urlopen(base + route, timeout=5)
                    self.assertEqual(caught.exception.code, 404)
                    caught.exception.close()
            finally:
                server.shutdown()
                thread.join()


if __name__ == '__main__':
    unittest.main()
