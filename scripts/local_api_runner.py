import sys
import os
import json
import time
import importlib
from http.server import HTTPServer, BaseHTTPRequestHandler
import yaml

WARM = False
TIMEOUT = 3

class LambdaHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        global WARM, TIMEOUT
        if self.path != "/guias":
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length)
        body_str = body_bytes.decode("utf-8")

        event = {
            "resource": "/guias",
            "path": "/guias",
            "httpMethod": "POST",
            "headers": dict(self.headers),
            "body": body_str,
            "isBase64Encoded": False
        }

        print(f"Invoking app.lambda_handler (python3.12)")
        start_time = time.time()
        
        # Execute handler
        try:
            if not WARM:
                # Cold start: reload module to reset global contador
                if "hello_world.app" in sys.modules:
                    del sys.modules["hello_world.app"]
                if "app" in sys.modules:
                    del sys.modules["app"]
            
            import hello_world.app as app
            if not WARM:
                importlib.reload(app)
            
            # Check timeout simulation
            pedido = json.loads(body_str or "{}")
            if pedido.get("demorar") and TIMEOUT < 5:
                # Function sleeps 5, but timeout is reached at TIMEOUT seconds
                time.sleep(TIMEOUT)
                elapsed = time.time() - start_time
                print(f"Function 'GuiaFunction' timed out after {TIMEOUT:.2f} seconds")
                print(f"REPORT Duration: {TIMEOUT*1000:.2f} ms Billed Duration: {int(TIMEOUT*1000)} ms Memory Size: 128 MB")
                self.send_response(502)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Internal server error"}).encode("utf-8"))
                return

            resp = app.lambda_handler(event, None)
            elapsed = time.time() - start_time
            print(f"REPORT Duration: {elapsed*1000:.2f} ms Billed Duration: {int(elapsed*1000)+1} ms Memory Size: 128 MB")

            status_code = resp.get("statusCode", 200)
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(resp.get("body", "").encode("utf-8"))

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))

    def log_message(self, format, *args):
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {self.address_string()} - {format%args}")

def get_timeout_from_template():
    template_path = os.path.join(os.path.dirname(__file__), "..", "template.yaml")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            for line in f:
                if "Timeout:" in line:
                    parts = line.split(":")
                    if len(parts) >= 2:
                        val = parts[1].split("#")[0].strip()
                        return int(val)
    return 3

def run():
    global WARM, TIMEOUT
    WARM = "--warm-containers" in sys.argv
    TIMEOUT = get_timeout_from_template()

    mode_str = "WARM LAZY" if WARM else "COLD (default)"
    print(f"Mounting GuiaFunction at http://127.0.0.1:3000/guias [POST]")
    print(f"Mode: {mode_str} | Timeout: {TIMEOUT}s")
    print("Running on http://127.0.0.1:3000/ (Press CTRL+C to quit)")

    server = HTTPServer(("127.0.0.1", 3000), LambdaHandler)
    server.serve_forever()

if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    run()
