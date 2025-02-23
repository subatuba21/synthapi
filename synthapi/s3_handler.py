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
        self.bucket_url = os.getenv('SUBHA_BUCKET_URL')
        self.lambda_url = os.getenv('LAMBDA_URL')
        
        if not self.bucket_url:
            raise ValueError("SYNTHAPI_BUCKET_URL environment variable is not set")
        if not self.lambda_url:
            raise ValueError("LAMBDA_URL environment variable is not set")
            
        self.bucket_url = self.bucket_url.rstrip('/')
    
    def upload_file(self, file_path: Path, dest_name: str) -> bool:
        """
        Upload a file to S3 in the appropriate folder based on file type
        
        Args:
            file_path (Path): Path to the local file
            dest_name (str): Destination name in S3
            
        Returns:
            bool: True if upload successful, False otherwise
        """
        try:
            if not file_path.exists():
                print(f"Error: File {file_path} does not exist")
                return False
            
            # Determine subfolder based on file type
            if dest_name.endswith('.json'):
                subfolder = 'schemas'
            elif dest_name.endswith('_data.txt'):
                subfolder = 'raw'
            else:
                print(f"Error: Unsupported file type for {dest_name}")
                return False
            
            # Construct the full S3 URL with appropriate subfolder
            url = f"{self.bucket_url}/{subfolder}/{dest_name}"
            
            # Read file content
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Determine content type
            content_type = 'application/json' if dest_name.endswith('.json') else 'text/plain'
            
            # Upload to S3
            response = requests.put(
                url,
                data=content,
                headers={'Content-Type': content_type}
            )
            
            if response.status_code in [200, 201]:
                print(f"✓ Successfully uploaded {dest_name} to {subfolder}/")
                return True
            else:
                print(f"✗ Error uploading {dest_name}: Status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ Error uploading {dest_name}: {str(e)}")
            return False

    def initialize_database(self, api_name: str) -> bool:
        """
        Initialize the database for an API by calling the Lambda function
        
        Args:
            api_name (str): Name of the API to initialize
            
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Construct Lambda URL with API name parameter
            lambda_request_url = f"{self.lambda_url}?API_NAME={api_name}"
            
            # Make POST request to Lambda
            response = requests.post(lambda_request_url)
            
            if response.status_code in [200, 201]:
                print(f"✓ Successfully initialized database for {api_name}")
                return True
            else:
                print(f"✗ Error initializing database: Status {response.status_code}")
                if response.text:
                    print(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Error initializing database: {str(e)}")
            return False

    def init_api(self, name: str, spec_path: Path, data_path: Path) -> bool:
        """
        Initialize an API by uploading files to S3 and initializing the database
        
        Args:
            name (str): API name
            spec_path (Path): Path to the OpenAPI spec JSON file
            data_path (Path): Path to the data file
            
        Returns:
            bool: True if all operations successful, False otherwise
        """
        try:
            # Upload spec file
            spec_success = self.upload_file(spec_path, f"{name}.json")
            if not spec_success:
                return False

            # Upload data file
            data_success = self.upload_file(data_path, f"{name}_data.txt")
            if not data_success:
                return False

            # Initialize database
            db_success = self.initialize_database(name)
            if not db_success:
                print("⚠️ Warning: Files uploaded but database initialization failed")
                return False

            return True

        except Exception as e:
            print(f"✗ Error during API initialization: {str(e)}")
            return False