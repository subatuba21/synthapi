import typer
import http.server
import socketserver
import webbrowser
import os
import json
from pathlib import Path
from .parser import DocParser

# Initialize typer with an explicit name
app = typer.Typer(name="synthapi")

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.parser = DocParser()
        super().__init__(*args, directory=str(Path(__file__).parent / 'static'), **kwargs)
    
    def _send_cors_headers(self):
        """Add CORS headers for API requests"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def do_OPTIONS(self):
        """Handle preflight CORS requests"""
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        if self.path == '/save':
            # Save to current working directory
            with open('openapi.json', 'w') as f:
                json.dump(data, f, indent=2)
            
            self.send_response(200)
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(b'Saved successfully')
            
        elif self.path == '/parse':
            try:
                # Parse the documentation using DocParser
                parameters = self.parser.parse_documentation(
                    documentation=data.get('documentation', ''),
                    method=data.get('method', 'GET'),
                    path=data.get('path', '')
                )
                
                # Send the response
                self.send_response(200)
                self._send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(parameters).encode('utf-8'))
                
            except Exception as e:
                self.send_response(500)
                self._send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': str(e)
                }).encode('utf-8'))

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