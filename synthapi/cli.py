import typer
import http.server
import socketserver
import webbrowser
import os
import json
from pathlib import Path

# Initialize typer with an explicit name
app = typer.Typer(name="synthapi")

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent / 'static'), **kwargs)
    
    def do_POST(self):
        if self.path == '/save':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            spec_data = json.loads(post_data.decode('utf-8'))
            
            # Save to current working directory
            with open('openapi.json', 'w') as f:
                json.dump(spec_data, f, indent=2)
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Saved successfully')

def start_server():
    """Open the OpenAPI specification generator form"""
    PORT = 8000
    
    # Start the server in a separate thread
    with socketserver.TCPServer(("", PORT), RequestHandler) as httpd:
        print(f"Serving form at http://localhost:{PORT}")
        print("Press Ctrl+C to stop the server")
        
        # Open the browser
        webbrowser.open(f'http://localhost:{PORT}')
        
        # Serve until interrupted
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.shutdown()

@app.callback()
def main():
    """A tool for generating OpenAPI specifications and mocking APIs"""
    pass

@app.command()
def generate():
    """Generate an OpenAPI specification using a web form"""
    start_server()

if __name__ == "__main__":
    app()