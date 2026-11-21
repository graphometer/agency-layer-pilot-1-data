#!/usr/bin/env python3
"""Local dev server for asset builds.

Serves the assets over loopback so the packer fetches them the same way CI
does. Usage: dev_server.py RUN_NUMBER. The port is written to
.server_ready once the server is up.
"""
import http.server
import socket
import struct
import sys

ASSETS = {
    "app.css": b"/* app styles */\nbody { margin: 0; }\n",
    "app.js": b"console.log('app');\n",
    "index.html": b"<html><body>webfront</body></html>\n",
    "logo.svg": b"<svg xmlns='http://www.w3.org/2000/svg'></svg>\n",
    "vendor.js": b"/* vendor bundle */\n",
}


class Handler(http.server.BaseHTTPRequestHandler):
    reset_run = 0

    def log_message(self, *args):
        pass

    def do_GET(self):
        name = self.path.lstrip("/")
        names = sorted(ASSETS)
        if name == "":
            # Index: the asset list this server is serving, one per line.
            index = ("\n".join(names) + "\n").encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(index)))
            self.end_headers()
            self.wfile.write(index)
            return
        # One asset per run drops the connection without a response; which
        # asset drops moves with the run number.
        if name == names[self.reset_run % len(names)]:
            self.connection.setsockopt(
                socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
            self.connection.close()
            return
        body = ASSETS.get(name)
        if body is None:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    run = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    Handler.reset_run = run
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    with open(".server_ready", "w") as fh:
        fh.write(str(server.server_address[1]))
    server.serve_forever()


if __name__ == "__main__":
    main()
