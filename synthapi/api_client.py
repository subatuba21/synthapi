import json
from pathlib import Path
import requests
import typer
import os
from dotenv import load_dotenv

load_dotenv()

# Get Lambda URL from environment
LAMBDA_GET_URL = os.getenv('LAMBDA_GET_URL', 'https://u7kdlpmkuocxml5jy4a4jrpclu0gyosv.lambda-url.us-east-1.on.aws/')

def load_api_spec(api_name, generated_api_dir):
    """Load and parse an API specification file"""
    spec_path = generated_api_dir / f"{api_name}.json"
    if not spec_path.exists():
        return None
        
    with open(spec_path) as f:
        return json.load(f)

def validate_parameters(params, endpoint_spec):
    """Validate provided parameters against the endpoint specification"""
    # Extract parameter specifications from the endpoint
    spec_params = endpoint_spec.get('parameters', [])
    
    # Create a map of parameter names to their specifications
    param_specs = {p['name']: p for p in spec_params}
    
    # Check for required parameters
    for param_name, param_spec in param_specs.items():
        if param_spec.get('required', False) and param_name not in params:
            return False, f"Missing required parameter: {param_name}"
    
    # Validate provided parameters
    for param_name, param_value in params.items():
        if param_name not in param_specs:
            return False, f"Unknown parameter: {param_name}"
            
        param_spec = param_specs[param_name]
        param_schema = param_spec.get('schema', {})
        
        # Type validation
        param_type = param_schema.get('type')
        try:
            if param_type == 'number':
                float(param_value)
            elif param_type == 'integer':
                int(param_value)
            elif param_type == 'boolean':
                if param_value.lower() not in ['true', 'false', '1', '0']:
                    return False, f"Invalid boolean value for {param_name}: {param_value}"
        except ValueError:
            return False, f"Invalid {param_type} value for {param_name}: {param_value}"
            
        # Range validation for numeric types
        if param_type in ['number', 'integer']:
            num_val = float(param_value)
            if 'minimum' in param_schema and num_val < param_schema['minimum']:
                return False, f"{param_name} must be >= {param_schema['minimum']}"
            if 'maximum' in param_schema and num_val > param_schema['maximum']:
                return False, f"{param_name} must be <= {param_schema['maximum']}"
                
        # Enum validation
        if 'enum' in param_schema and param_value not in param_schema['enum']:
            return False, f"Invalid value for {param_name}. Must be one of: {', '.join(param_schema['enum'])}"
    
    return True, None

def make_request(api_name, endpoint, params):
    """Make the GET request to the Lambda endpoint"""
    # Add API name and endpoint to parameters
    request_params = {
        'API_NAME': api_name,
        'ENDPOINT': endpoint,
        **params
    }
    
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'synthapi-client/0.1.0'
    }
    
    response = requests.get(
        LAMBDA_GET_URL.rstrip('/'),
        params=request_params,
        headers=headers
    )
    
    return response

def get(
    api_name=typer.Option(..., "--api", "-a", help="Name of the API to query"),
    endpoint=typer.Option(..., "--endpoint", "-e", help="Endpoint path (e.g. /v1/users)"),
    location=typer.Option(None, "--location", help="Location parameter"),
    term=typer.Option(None, "--term", help="Search term"),
    latitude=typer.Option(None, "--latitude", help="Latitude for location"),
    longitude=typer.Option(None, "--longitude", help="Longitude for location")
):
    """Make a GET request to a registered API endpoint with parameter validation"""
    # Get the generated APIs directory from the package location
    api_dir = Path(__file__).parent / "generated_apis"
    
    # Load the API specification
    spec = load_api_spec(api_name, api_dir)
    
    if not spec:
        typer.echo(f"❌ Error: No specification found for API '{api_name}'")
        raise typer.Exit(1)
    
    # Find the endpoint specification
    endpoint_spec = spec.get('paths', {}).get(endpoint, {}).get('get')
    if not endpoint_spec:
        typer.echo(f"❌ Error: No GET method found for endpoint '{endpoint}'")
        raise typer.Exit(1)
        
    # Build parameters dictionary
    param_dict = {}
    if location:
        param_dict['location'] = location
    if term:
        param_dict['term'] = term
    if latitude:
        param_dict['latitude'] = latitude
    if longitude:
        param_dict['longitude'] = longitude
    
    # Validate parameters
    is_valid, error = validate_parameters(param_dict, endpoint_spec)
    if not is_valid:
        typer.echo(f"❌ Error: {error}")
        raise typer.Exit(1)
    
    # Make the request
    try:
        response = make_request(api_name, endpoint, param_dict)
        
        # Print response details
        typer.echo(f"\nRequest URL: {response.url}")
        typer.echo(f"Status: {response.status_code}")
        typer.echo("\nResponse:")
        try:
            # Try to pretty print JSON response
            typer.echo(json.dumps(response.json(), indent=2))
        except:
            # Fallback to raw text if not JSON
            typer.echo(response.text)
            
    except requests.RequestException as e:
        typer.echo(f"❌ Error making request: {str(e)}")
        raise typer.Exit(1)