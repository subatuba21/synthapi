# SynthAPI

A tool for local API mocking with dynamic data generation. SynthAPI helps you create, initialize, and manage mock APIs using OpenAPI specifications and AI-generated data.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/synthapi.git
cd synthapi
```

2. Install in development mode:
```bash
pip install -e .
```

## Environment Setup

Before using SynthAPI, make sure to set up the following environment variables:

```bash
OPENAI_API_KEY=your_openai_api_key
SUBHA_BUCKET_URL=your_s3_bucket_url
LAMBDA_URL=your_lambda_function_url
```

You can use a `.env` file to store these variables.

## CLI Commands

### Generate an API Specification

Create a new OpenAPI specification using an interactive web form:

```bash
synthapi generate --name your_api_name
```

This will:
- Open a web form in your browser
- Allow you to define endpoints, parameters, and documentation
- Generate and save an OpenAPI 3.0 specification

### Initialize an API

Initialize an API by uploading its specification and setting up the database:

```bash
synthapi init --name your_api_name [--data "Optional context data for LLM"]
```

This will:
- Upload the OpenAPI specification to S3
- Upload any provided context data
- Initialize the database through Lambda
- Mark the API as initialized in the registry

### Extend an API

Update an existing API's data and database:

```bash
synthapi extend --name your_api_name --data "New data prompt for the API"
```

This will:
- Upload a new data prompt file to S3
- Trigger the database update through Lambda
- Only works with initialized APIs

### List Available APIs

View available APIs in the registry:

```bash
synthapi list              # Show uninitialized APIs only
synthapi list --all       # Show all APIs with their status
```

### Clean Registry

Remove all registered APIs and generated files:

```bash
synthapi clean            # With confirmation prompt
synthapi clean --force   # Skip confirmation
```

## API Parameters

When defining API parameters in the web form, you can:
- Set parameter names, types, and descriptions
- Mark parameters as required
- Define constraints (min/max values, enums)
- Parse parameter documentation automatically

## Example Parameter Documentation

Here's an example of parameter documentation that can be parsed:

```
location (required): The location to search for businesses.
term (optional): Search term (e.g. food, restaurants).
radius (optional): Search radius in meters. Max value is 40000.
```

## Flow

1. Generate API spec using the web form (`generate`)
2. Initialize the API with optional context (`init`)
3. Extend the API's data as needed (`extend`)

## Error Handling

The CLI provides clear error messages for common issues:
- Missing environment variables
- Invalid API names
- Network/S3 upload failures
- Database initialization errors

## Development

The project uses:
- Typer for CLI interface
- OpenAI GPT-4 for documentation parsing
- React for the web form interface
- S3 for specification and data storage
- Lambda for database operations