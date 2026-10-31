"""Local-only fixture for the real RangeStream: no YouTube requests."""
import http.server
import subprocess
import threading
from collections import Counter

counts = Counter()
class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass
    def do_GET(self):
        counts[self.path] += 1
        kind = self.path.split('?')[0]
        status = int(kind[1:])
        if status == 500 and counts[self.path] > 1:
            status = 206
        self.send_response(status)
        if status == 206:
            self.send_header('Content-Range', 'bytes 0-3/4')
        self.send_header('Content-Length', '4' if status == 206 else '0')
        self.end_headers()
        if status == 206:
            self.wfile.write(b'RIFF')

server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
for status, expected_count in [(403, 1), (401, 1), (429, 1), (500, 2), (206, 1)]:
    path = f'/{status}?clen=4'
    subprocess.run(['build/video-startup/range-test', f'http://127.0.0.1:{server.server_port}{path}', str(status)], check=True, timeout=5)
    assert counts[path] == expected_count, (status, counts[path])
server.shutdown()
print('PASS real RangeStream: authorization refusal immediately stops after one request; transient 500 recovers; successful range bytes retained')
