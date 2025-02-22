# SynthAPI

A tool for local API mocking and OpenAPI specification generation. SynthAPI helps you create OpenAPI specifications from documentation and set up mock API servers for development and testing.

## Features

- Generate OpenAPI 3.0 specifications using a web-based form
- Parse API documentation using GPT-4 to extract parameters
- Save specifications in OpenAPI JSON format
- Easy-to-use command-line interface

## Installation

### Prerequisites

- Python 3.7 or higher
- OpenAI API key for documentation parsing

### Steps

1. Clone the repository:
```bash
git clone <your-repo-url>
cd synthapi
```

2. Install the package:
```bash
pip install -e .
```

3. Set up your environment variables:
Create a `.env` file in your project root:
```bash
OPENAI_API_KEY=your_api_key_here
```

## Usage

### CLI Commands

Currently, SynthAPI supports the following commands:

#### Generate OpenAPI Specification

Start the web interface for creating OpenAPI specifications:

```bash
synthapi generate
```

This will:
1. Start a local server on port 8000
2. Open your default browser to the form interface
3. Allow you to create and save OpenAPI specifications

### Web Interface

The web interface provides a form-based approach to creating API specifications:

1. Click "Add Endpoint" to create a new endpoint definition
2. Fill in the endpoint details:
   - Name: A descriptive name for the endpoint
   - Method: HTTP method (GET, POST, PUT, DELETE)
   - Path: The API path (e.g., /v3/businesses/search)
   
3. Add API documentation:
   - Paste your API documentation text
   - Click "Parse Documentation" to automatically extract parameters
   
4. Add or modify parameters:
   - Name, type, and whether it's required
   - Description and constraints
   - For numeric types, specify minimum and maximum values
   
5. Click "Generate OpenAPI Spec" to save the specification
   - The specification will be saved as `openapi.json` in your current directory

### Example

Here's an example of API documentation that can be parsed:

```
location (required): The location to search for businesses. Example: 'NYC'
term (optional): Search term (e.g. food, restaurants).
radius (optional): Search radius in meters. Max value is 40000.
```

After parsing, this will generate parameter definitions in the OpenAPI specification format.

## Development

### Project Structure

```
synthapi/
├── __init__.py
├── cli.py                 # Main CLI entry point
├── parser.py             # API documentation parser
├── static/              # Frontend assets
│   ├── index.html
│   └── form.js
```

### Adding New Features

1. Create new Python modules for your features
2. Add new CLI commands in `cli.py`
3. Update dependencies in `pyproject.toml`
4. Test locally using `pip install -e .`

### Running Tests

```bash
# TODO: Add testing instructions
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Troubleshooting

### Common Issues

1. **Server Already Running**
   If you get a port conflict error when running `synthapi generate`, ensure no other service is using port 8000.

2. **Parse Documentation Not Working**
   Make sure you've set up your `OPENAI_API_KEY` in the `.env` file correctly.

3. **Browser Not Opening**
   The tool attempts to open your default browser automatically. If this doesn't work, manually navigate to `http://localhost:8000`.

### Getting Help

If you encounter any issues:
1. Check the troubleshooting section above
2. Look for existing issues in the GitHub repository
3. Create a new issue with details about your problem

## Roadmap

Future features planned:
- Mock API server generation from OpenAPI specs
- OpenAPI specification validation
- Custom response templating
- Multiple specification format support (YAML, JSON)