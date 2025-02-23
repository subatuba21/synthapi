import typer
import http.server
import socketserver
import webbrowser
import os
import json
import socket
import time
from pathlib import Path
from .parser import DocParser
from .s3_handler import S3Handler
from .api_registry import (
    get_available_specs,
    add_api_to_registry,
    get_all_specs,
    mark_api_as_initialized,
    clean_registry
)
from .api_client import get

# Initialize typer app
app = typer.Typer(name="synthapi")

# Define the directory for generated APIs
GENERATED_API_DIR = Path(__file__).parent / "generated_apis"
GENERATED_API_DIR.mkdir(exist_ok=True)

def is_port_in_use(port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('', port))
            return False
        except OSError:
            return True

def find_available_port(start_port=8000, max_attempts=10):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            return port
    return None

def get_current_api_name():
    """Retrieve the current API name from the temporary file"""
    temp_file = GENERATED_API_DIR / "current_api_name.txt"
    if temp_file.exists():
        with open(temp_file, "r") as f:
            return f.read().strip()
    return None

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.parser = DocParser()
        super().__init__(*args, directory=str(Path(__file__).parent / "static"), **kwargs)

    def _send_cors_headers(self):
        """Add CORS headers for API requests"""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        """Handle preflight CORS requests"""
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/api-name":
            api_name = get_current_api_name()
            if api_name:
                self.send_response(200)
                self._send_cors_headers()
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"name": api_name}).encode("utf-8"))
                return
            else:
                self.send_response(404)
                self.end_headers()
                return
        
        super().do_GET()

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode("utf-8"))

        if self.path == "/save":
            api_name = get_current_api_name()
            if not api_name:
                self.send_response(400)
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(b"Error: No API name specified")
                return

            # Save the API specification JSON
            api_file_path = GENERATED_API_DIR / f"{api_name}.json"
            with open(api_file_path, "w") as f:
                json.dump(data, f, indent=2)

            self.send_response(200)
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(b"API Spec Saved Successfully")
            
            # Signal to the server to shutdown after sending response
            self.server.should_shutdown = True

        elif self.path == "/parse":
            try:
                parameters = self.parser.parse_documentation(
                    documentation=data.get("documentation", ""),
                    method=data.get("method", "GET"),
                    path=data.get("path", ""),
                )

                self.send_response(200)
                self._send_cors_headers()
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(parameters).encode("utf-8"))

            except Exception as e:
                self.send_response(500)
                self._send_cors_headers()
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

class ShutdownableHTTPServer(socketserver.TCPServer):
    allow_reuse_address = True
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.should_shutdown = False

    def service_actions(self):
        """Called between requests, check if we should shutdown"""
        if self.should_shutdown:
            self.shutdown()

def start_server():
    """Start the local server for the OpenAPI specification generator form"""
    # Find an available port
    port = find_available_port()
    if not port:
        print("❌ Error: Could not find an available port")
        raise typer.Exit(1)

    try:
        with ShutdownableHTTPServer(("", port), RequestHandler) as httpd:
            print(f"Serving form at http://localhost:{port}")
            print("Server will automatically stop after saving the API spec")
            print("Press Ctrl+C to stop the server manually")
            
            webbrowser.open(f"http://localhost:{port}")
            
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nShutting down server...")
            finally:
                httpd.server_close()
                
                # Small delay to ensure socket is fully closed
                time.sleep(0.1)
    except Exception as e:
        print(f"❌ Error starting server: {str(e)}")
        raise typer.Exit(1)

@app.command()
def clean(
    force=typer.Option(False, "--force", "-f", help="Clean without confirmation")
):
    """Clean the API registry and remove all generated files"""
    if not force:
        confirm = typer.confirm(
            "⚠️ This will delete all registered APIs and generated files. Continue?",
            abort=True
        )
    
    try:
        clean_registry()
        print("✅ Successfully cleaned registry and removed generated files")
    except Exception as e:
        print(f"❌ Error cleaning registry: {str(e)}")
        raise typer.Exit(1)
    
@app.command()
def generate(
    name=typer.Option(..., "--name", "-n", help="Project name (must not contain spaces)")
):
    """Generate an OpenAPI specification using a web form"""
    if " " in name:
        print("Error: Project name cannot contain spaces")
        raise typer.Exit(1)

    # Save the API name for the web form to access
    with open(GENERATED_API_DIR / "current_api_name.txt", "w") as f:
        f.write(name)

    # Add the API to the registry
    add_api_to_registry(name)

    print(f"Generating OpenAPI specification for project: {name}")
    start_server()

@app.command()
def init(
    name=typer.Option(..., "--name", "-n", help="Project name (must exist in registry)"),
    data=typer.Option(None, "--data", "-d", help="Context data for LLM (optional)")
):
    """Initialize an API by sending its spec to S3 and setting up the database"""
    # Get all specs and their status
    all_specs = get_all_specs()
    available_specs = get_available_specs()
    
    if name not in all_specs:
        print(f"❌ Error: '{name}' is not in the registry.")
        print("\nAvailable APIs for initialization:")
        if available_specs:
            for spec in available_specs:
                print(f"  • {spec}")
        else:
            print("  No APIs available for initialization")
        raise typer.Exit(1)
    
    if all_specs[name]:  # If already initialized
        print(f"❌ Error: '{name}' has already been initialized.")
        print("\nAvailable APIs for initialization:")
        if available_specs:
            for spec in available_specs:
                print(f"  • {spec}")
        else:
            print("  No APIs available for initialization")
        raise typer.Exit(1)

    try:
        s3_handler = S3Handler()
        api_spec_path = GENERATED_API_DIR / f"{name}.json"
        data_file_path = GENERATED_API_DIR / f"{name}_data.txt"

        # Ensure the OpenAPI spec exists
        if not api_spec_path.exists():
            print(f"❌ Error: No generated API spec found for '{name}'.")
            raise typer.Exit(1)

        # Write the data file (empty if no -d flag provided)
        with open(data_file_path, "w") as f:
            f.write(data if data else "")

        # Initialize the API (upload files and setup database)
        success = s3_handler.init_api(name, api_spec_path, data_file_path)

        if success:
            # Mark the API as initialized in the registry
            if mark_api_as_initialized(name):
                print(f"✅ Successfully initialized {name}:")
                print(f"  • Uploaded {name}.json to schemas/")
                print(f"  • Uploaded {name}_data.txt to raw/")
                print(f"  • Initialized database")
                print(f"  • Marked as initialized in registry")
                
                # Show remaining available APIs
                remaining_specs = get_available_specs()
                if remaining_specs:
                    print("\nRemaining APIs available for initialization:")
                    for spec in remaining_specs:
                        print(f"  • {spec}")
                else:
                    print("\nNo more APIs available for initialization")
            else:
                print("⚠️ Warning: API initialized but failed to mark as initialized in registry")
        else:
            print("❌ Error: Failed to initialize API")
            raise typer.Exit(1)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise typer.Exit(1)
    
@app.command()
def extend(
    name: str = typer.Option(..., "--name", "-n", help="API name to extend"),
    data: str = typer.Option(..., "--data", "-d", help="Data prompt for extending the API"),
):
    """Extend an API's data by uploading a new data prompt and updating the database"""
    try:
        # Check if API exists and is initialized
        all_specs = get_all_specs()
        if name not in all_specs:
            print(f"❌ Error: '{name}' is not in the registry.")
            return
        
        if not all_specs[name]:
            print(f"❌ Error: '{name}' has not been initialized yet.")
            return

        # Create and upload data file
        s3_handler = S3Handler()
        data_file_path = GENERATED_API_DIR / f"{name}_data.txt"
        
        # Write the data prompt to a file
        with open(data_file_path, "w") as f:
            f.write(data)

        # Upload the data file to S3
        if s3_handler.upload_file(data_file_path, f"{name}_data.txt"):
            # Initialize database with new data
            if s3_handler.initialize_database(name):
                print(f"✅ Successfully extended {name}:")
                print(f"  • Uploaded new {name}_data.txt to raw/")
                print(f"  • Updated database with new data")
            else:
                print("❌ Error: Failed to update database")
                raise typer.Exit(1)
        else:
            print("❌ Error: Failed to upload data file")
            raise typer.Exit(1)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise typer.Exit(1)
    
@app.command()
def list(
    all=typer.Option(False, "--all", "-a", help="Show all APIs including initialized ones")
):
    """List available APIs that can be initialized"""
    if all:
        specs = get_all_specs()
        if not specs:
            print("No APIs found in registry")
            return
        
        print("All registered APIs:")
        for name, initialized in specs.items():
            status = "✓ Initialized" if initialized else "• Available"
            print(f"  {status}: {name}")
    else:
        specs = get_available_specs()
        if not specs:
            print("No APIs available for initialization")
            return
        
        print("Available APIs for initialization:")
        for spec in specs:
            print(f"  • {spec}")

# Add the get command
app.command()(get)

if __name__ == "__main__":
    app()