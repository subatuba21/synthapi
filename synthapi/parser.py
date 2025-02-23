import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class DocParser:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = OpenAI(api_key=api_key)

    def create_prompt(self, documentation: str, method: str, path: str) -> str:
        return f"""You are tasked with parsing API parameter documentation into a structured format.
The documentation has parameters separated by newlines.

Parse each parameter to identify:
1. Name (usually the first word or token in the parameter block)
2. Type (infer as string, number, integer, boolean, or array)
3. Required status (look for 'required', 'optional', '*Optional*', or contextual clues)
4. Description (preserve any markdown formatting)
5. Constraints (look for):
   - Minimum/maximum values or lengths
   - Allowed values or formats
   - Default values
   - Dependencies on other parameters
   - Business logic requirements

Input Documentation:
{documentation}

Endpoint: {method} {path}

Return a JSON array of parameters with this structure:
[
  {{
    "name": string,
    "type": "string" | "number" | "integer" | "boolean" | "array",
    "required": boolean,
    "description": string,
    "constraints": {{
      "min": number | null,
      "max": number | null,
      "default": any | null,
      "enum": array | null,
      "conditional_requirement": string | null
    }}
  }}
]

Be precise and maintain any markdown formatting in descriptions."""

    def parse_documentation(self, documentation: str, method: str, path: str) -> List[Dict[str, Any]]:
        """Parse API documentation into structured parameter data"""
        try:
            # Clean and normalize input
            documentation = '\n'.join(
                line.strip() for line in documentation.splitlines() if line.strip()
            )
            
            # Request GPT-4 analysis
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise API documentation parser. Extract parameter information and return it as valid JSON only, with no additional text."
                    },
                    {
                        "role": "user",
                        "content": self.create_prompt(documentation, method, path)
                    }
                ],
                temperature=0.1  # Low temperature for consistent results
            )
            
            # Extract and parse response
            content = response.choices[0].message.content
            parsed_data = json.loads(content)
            
            # Handle both list and dict responses
            parameters = parsed_data if isinstance(parsed_data, list) else parsed_data.get('parameters', [])
            cleaned_parameters = []
            
            for param in parameters:
                cleaned_param = self._clean_parameter(param)
                if cleaned_param["name"]:  # Only include if name exists
                    cleaned_parameters.append(cleaned_param)
            
            # Check for warnings
            warnings = self.validate_parameters(cleaned_parameters)
            if warnings:
                print("\nWarnings during parsing:")
                for warning in warnings:
                    print(f"- {warning}")
            
            return cleaned_parameters
            
        except Exception as e:
            print(f"Error parsing documentation: {str(e)}")
            return []

    def _clean_parameter(self, param: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize a single parameter"""
        return {
            "name": param.get("name", "").strip(),
            "type": param.get("type", "string").lower(),
            "required": bool(param.get("required", False)),
            "description": param.get("description", "").strip(),
            "constraints": {
                "min": self._safe_numeric(param.get("constraints", {}).get("min")),
                "max": self._safe_numeric(param.get("constraints", {}).get("max")),
                "default": param.get("constraints", {}).get("default"),
                "enum": param.get("constraints", {}).get("enum", []),
                "conditional_requirement": param.get("constraints", {}).get("conditional_requirement")
            }
        }

    def _safe_numeric(self, value: Any) -> Optional[float]:
        """Safely convert a value to a number"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def validate_parameters(self, parameters: List[Dict[str, Any]]) -> List[str]:
        """Validate parameters and return warnings"""
        warnings = []
        
        for param in parameters:
            # Required fields
            if not param.get("name"):
                warnings.append("Parameter found with no name")
                continue
                
            if not param.get("description"):
                warnings.append(f"No description for parameter '{param['name']}'")
            
            # Type validation
            valid_types = {"string", "number", "integer", "boolean", "array"}
            if param.get("type") not in valid_types:
                warnings.append(f"Invalid type '{param.get('type')}' for parameter '{param['name']}'")
            
            # Constraint validation
            constraints = param.get("constraints", {})
            if constraints.get("min") is not None and constraints.get("max") is not None:
                if constraints["min"] > constraints["max"]:
                    warnings.append(f"Invalid range for '{param['name']}': min > max")
            
            # Enum validation
            if constraints.get("enum"):
                if not isinstance(constraints["enum"], list):
                    warnings.append(f"Invalid enum format for '{param['name']}'")
                elif not constraints["enum"]:
                    warnings.append(f"Empty enum list for '{param['name']}'")
            
            # Conditional requirements
            if constraints.get("conditional_requirement"):
                if not isinstance(constraints["conditional_requirement"], str):
                    warnings.append(f"Invalid conditional requirement format for '{param['name']}'")
        
        return warnings