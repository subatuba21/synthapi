import requests
import json
import os
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class S3Handler:
    def __init__(self):
        bucket_url = os.getenv('SUBHA_BUCKET_URL')
        if not bucket_url:
            raise ValueError("SYNTHAPI_BUCKET_URL environment variable is not set")
        self.bucket_url = bucket_url.rstrip('/')
    
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
    
    def get_upload_urls(self, project_name: str) -> Tuple[str, str]:
        """Generate URLs for raw text and spec files"""
        if not project_name:
            raise ValueError("Project name is required")
            
        text_url = f"{self.bucket_url}/raw/{project_name}_raw.txt"
        spec_url = f"{self.bucket_url}/schemas/{project_name}_spec.json"
        
        return text_url, spec_url
    
    def upload_init_files(self, raw_text: str, project_name: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Upload both raw text and generated OpenAPI spec for the init command
        
        Args:
            raw_text: The raw API documentation text
            project_name: The required project name (no spaces allowed)
            
        Returns:
            Tuple of (success, text_url, spec_url)
        """
        try:
            # Generate URLs for both files
            text_url, spec_url = self.get_upload_urls(project_name)
            
            # Upload raw text
            text_response = requests.put(
                text_url,
                data=raw_text,
                headers={'Content-Type': 'text/plain'}
            )
            
            if text_response.status_code not in [200, 201]:
                print(f"✗ Error uploading raw text: Status {text_response.status_code}")
                return False, None, None
            
            # Read and upload the existing OpenAPI spec
            spec_data = self.read_spec()
            if not spec_data:
                print("✗ Error: Could not read openapi.json")
                return False, None, None
            
            # Upload spec
            spec_response = requests.put(
                spec_url,
                json=spec_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if spec_response.status_code not in [200, 201]:
                print(f"✗ Error uploading spec: Status {spec_response.status_code}")
                return False, None, None
            
            print("✓ Successfully uploaded files:")
            print(f"Raw documentation: {text_url}")
            print(f"OpenAPI spec: {spec_url}")
            
            return True, text_url, spec_url
            
        except requests.RequestException as e:
            print(f"✗ Error uploading to S3: {str(e)}")
            return False, None, None
        except Exception as e:
            print(f"✗ Unexpected error: {str(e)}")
            return False, None, None
    
    def upload_spec(self) -> bool:
        """Upload existing openapi.json to the public S3 bucket schemas directory"""
        if not self.check_spec_exists():
            print("Error: openapi.json not found in current directory.")
            print("Please run 'synthapi generate' first to create the specification.")
            return False
        
        spec_data = self.read_spec()
        if not spec_data:
            return False
        
        try:
            # Upload to default schemas location
            response = requests.put(
                f"{self.bucket_url}/schemas/openapi.json",
                json=spec_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [200, 201]:
                print("✓ Successfully uploaded OpenAPI specification")
                print(f"Public URL: {self.bucket_url}/schemas/openapi.json")
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
            
    def download_spec(self, url: Optional[str] = None) -> Optional[dict]:
        """Download an OpenAPI spec from S3"""
        try:
            download_url = url if url else f"{self.bucket_url}/schemas/openapi.json"
            response = requests.get(download_url)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"✗ Error downloading spec: Status {response.status_code}")
                return None
                
        except requests.RequestException as e:
            print(f"✗ Error downloading spec: {str(e)}")
            return None
        except json.JSONDecodeError:
            print("✗ Error: Invalid JSON in downloaded spec")
            return None
        except Exception as e:
            print(f"✗ Unexpected error: {str(e)}")
            return None