import typer
import http.server
import socketserver
import webbrowser
import os
import json
from pathlib import Path
from .parser import DocParser

from .s3_handler import S3Handler
from typing import Optional

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

@app.command()
def init(
    data: str = typer.Option(..., "--data", "-d", help="Initial API documentation text"),
    name: str = typer.Option(..., "--name", "-n", help="Project name (no spaces allowed)")
):
    """Initialize a new API specification with documentation text"""
    # Validate that project name doesn't contain spaces
    if " " in name:
        print("Error: Project name cannot contain spaces")
        raise typer.Exit(1)
        
    try:
        # Initialize S3 handler
        s3_handler = S3Handler()
        
        # Upload both raw text and specification files
        success, text_url, spec_url = s3_handler.upload_init_files(data, name)
        
        # Exit with error if upload failed
        if not success:
            raise typer.Exit(1)
            
    except Exception as e:
        print(f"Error: {str(e)}")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()