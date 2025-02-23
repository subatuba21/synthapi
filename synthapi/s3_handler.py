import requests
import json
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class S3Handler:
    def __init__(self):
        bucket_url = os.getenv('SYNTHAPI_BUCKET_URL')
        if not bucket_url:
            raise ValueError("SYNTHAPI_BUCKET_URL environment variable is not set")
        self.bucket_url = f"{bucket_url}/schemas/openapi.json"
    
    def check_spec_exists(self) -> bool:
        """Check if openapi.json exists in current directory"""
        spec_path = Path('openapi.json')
        return spec_path.exists()
    
    def read_spec(self) -> Optional[dict]:
        """Read and validate the OpenAPI spec file"""
        try:
            with open('openapi.json', 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("✗ Error: Invalid JSON in openapi.json")
            return None
        except Exception as e:
            print(f"✗ Error reading specification: {str(e)}")
            return None
    
    def upload_spec(self) -> bool:
        """Upload openapi.json to the public S3 bucket schemas directory"""
        if not self.check_spec_exists():
            print("Error: openapi.json not found in current directory.")
            print("Please run 'synthapi generate' first to create the specification.")
            return False
        
        spec_data = self.read_spec()
        if not spec_data:
            return False
        
        try:
            # Upload directly to S3 bucket's schemas directory
            response = requests.put(
                self.bucket_url,
                json=spec_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [200, 201]:
                print("✓ Successfully uploaded OpenAPI specification")
                print(f"Public URL: {self.bucket_url}")
                return True
            else:
                print(f"✗ Error uploading to S3: Status {response.status_code}")
                return False
                
        except requests.RequestException as e:
            print(f"✗ Error uploading to S3: {str(e)}")
            return False
        except Exception as e:
            print(f"✗ Unexpected error: {str(e)}")
            return False