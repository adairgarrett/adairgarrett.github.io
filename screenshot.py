import sys
import os
import threading
import time
from http.server import SimpleHTTPRequestHandler, HTTPServer
from playwright.sync_api import sync_playwright

class EphemeralHTTPServer(threading.Thread):
    def __init__(self, directory):
        super().__init__()
        self.directory = directory
        self.server = None
        self.port = None

    def run(self):
        # Serve the specified directory
        handler = lambda *args, **kwargs: SimpleHTTPRequestHandler(*args, directory=self.directory, **kwargs)
        # Port 0 lets the OS pick an ephemeral free port
        self.server = HTTPServer(('127.0.0.1', 0), handler)
        self.port = self.server.server_port
        self.server.serve_forever()

    def shutdown(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()

def main():
    if len(sys.argv) < 3:
        print("Usage: python screenshot.py <html_file> <output_image_path> [viewport_width]")
        sys.exit(1)

    html_file = sys.argv[1]
    output_path = sys.argv[2]
    
    viewport_width = 1440
    if len(sys.argv) >= 4:
        try:
            viewport_width = int(sys.argv[3])
        except ValueError:
            print("Invalid viewport width, using default 1440")

    if not os.path.exists(html_file):
        print(f"Error: HTML file '{html_file}' not found.")
        sys.exit(1)

    # Get directory and file name
    dir_path = os.path.dirname(os.path.abspath(html_file))
    file_name = os.path.basename(html_file)

    print(f"Starting server in directory: {dir_path}")
    server_thread = EphemeralHTTPServer(dir_path)
    server_thread.start()

    # Wait for server to bind and start
    while server_thread.port is None:
        time.sleep(0.1)

    url = f"http://127.0.0.1:{server_thread.port}/{file_name}"
    print(f"Serving at {url}")

    try:
        with sync_playwright() as p:
            print("Launching browser...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": viewport_width, "height": 900},
                device_scale_factor=1
            )
            page = context.new_page()
            
            print(f"Navigating to {url}...")
            page.goto(url)
            
            print("Waiting for network idle (CDN / assets)...")
            page.wait_for_load_state("networkidle")
            time.sleep(1) # Extra buffer for layout and rendering
            
            print(f"Capturing screenshot to {output_path}...")
            page.screenshot(path=output_path, full_page=True)
            print("Screenshot captured successfully!")
            
            browser.close()
    except Exception as e:
        print(f"Error during screenshot capture: {e}")
    finally:
        print("Stopping server...")
        server_thread.shutdown()
        server_thread.join()

if __name__ == "__main__":
    main()
