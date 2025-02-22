import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class DocParser:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    def create_prompt(self, documentation: str, method: str, path: str) -> str:
        return f"""Given the following API documentation for a {method} endpoint at {path}, 
        extract all parameters and their details. For each parameter, identify:
        - name
        - type (string, number, integer, boolean, array)
        - whether it's required
        - description
        - any constraints (min, max, enum values)

        Return the response as a JSON array of parameters in this format:
        [{{
            "name": "parameter_name",
            "type": "parameter_type",
            "required": boolean,
            "description": "parameter_description",
            "constraints": {{
                "min": number or null,
                "max": number or null,
                "enum": [possible values] or null
            }}
        }}]

        API Documentation:
        {documentation}
        """

    def parse_documentation(self, documentation: str, method: str, path: str) -> List[Dict[str, Any]]:
        try:
            # Send to GPT for parsing
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful API documentation parser. Your task is to extract parameter information from API documentation and return it in a structured format."},
                    {"role": "user", "content": self.create_prompt(documentation, method, path)}
                ],
                response_format={ "type": "json_object" }
            )
            
            # Extract the JSON response
            content = response.choices[0].message.content
            parameters = json.loads(content).get('parameters', [])
            
            # Validate and clean up the parameters
            cleaned_parameters = []
            for param in parameters:
                cleaned_param = {
                    "name": param.get("name", ""),
                    "type": param.get("type", "string"),
                    "required": param.get("required", False),
                    "description": param.get("description", ""),
                    "constraints": {
                        "min": param.get("constraints", {}).get("min", None),
                        "max": param.get("constraints", {}).get("max", None),
                        "enum": param.get("constraints", {}).get("enum", [])
                    }
                }
                cleaned_parameters.append(cleaned_param)
            
            return cleaned_parameters
            
        except Exception as e:
            print(f"Error parsing documentation: {str(e)}")
            return []

# Example usage:
# parser = DocParser()
# parameters = parser.parse_documentation(
#     documentation="location (required): The location to search for businesses. Example: 'NYC'",
#     method="GET",
#     path="/v3/businesses/search"
# )