import json
import boto3
import re
from pinecone import Pinecone
import hashlib
import random
import sys

KEY = "pcsk_5fjTMD_94yGbMH2Ujw2d3CEqfyvByLqeswYEP4LGLePfYQzfsiEKK1RoY2Z7UX9qnQ3sq3"
IDX_NAME = "quickstart2"

# todo: change namespace based on the current API
NAMESPACE = "records"

def lambda_handler(event, context):
    # Create a Bedrock runtime client
    s3 = boto3.client('s3')
    bucket_name = 'gt-hacklytics-2025-synthapi'
    file_key = None
    prompt_addl_key = None

    file_key = "schemas/openapi.json"
    # Only process files in the schemas directory    
    prompt_addl_key = "raw/openapi.txt"
    
    print(f"Processing file: {file_key}")
    print(f"Processing prompt: {prompt_addl_key}")

    bedrock_runtime = boto3.client('bedrock-runtime', region_name="us-east-1")
    model_id = 'anthropic.claude-3-haiku-20240307-v1:0'
    s3.delete_object(Bucket=bucket_name, Key='output/result.json')

    try:
        # Invoke the model using the Bedrock runtime for the json
        print(file_key)
        response = s3.get_object(Bucket=bucket_name, Key=file_key)
        file_content = response['Body'].read().decode('utf-8')
        json_data = json.loads(file_content)
        print(file_key, "done")


         # Invoke the model using the Bedrock runtime for the response prompt
        print(prompt_addl_key)
        response_prompt = s3.get_object(Bucket=bucket_name, Key=prompt_addl_key)
        prompt_addl = response_prompt['Body'].read().decode('utf-8')
        print(prompt_addl)
        print(prompt_addl_key, "done")

        prompt = f"""You are an API based off of the OpenAPI schema provided in the XML tags 
            You will play the role of this API and generate samples in a JSON format abiding by the <schema> passed, so that the output returned is a properly formatted JSON file:
 
            {{
                1: <synthetic_1>,
                ...
                10: <synthetic_5>
            }}

            Your response will abide by the OpenAPI schema and represent a possible sample for this set.
            Encompass your response in the <resp></resp> tags and ensure it's in valid JSON formatting and a set of synthetic data samples, not code or any other form of response.
            You only respond in the format of a list in <resp> tags with each entry a JSON dict.
            <schema>{json_data}</schema> and here is additional information describing the synthetic data: 
            """ + prompt_addl

        

        # print(request_body)
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        
        
        # request_body["prompt"] = f"""make fake data for a schema  + {json_data}

        # Instructions:
        # 1. Create unique data entries that conform to this schema.
        # 2. Ensure all required fields are filled with realistic, varied data.
        # 3. For any field with constraints (e.g., min/max values, patterns), adhere to those constraints.
        # 4. If there are enum fields, use values from the provided options.
        # 5. For date/time fields, use realistic and varied dates/times.
        # 6. Ensure that relationships between fields (if any) are logically consistent.
        # 7. Output the data in valid JSON format."""


        # print("File content:" + file_content)
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body)
        )

        # Parse the response; assume the generated text is in 'generatedText'
        result = json.loads(response['body'].read())
        # generated_text = result.get("body", "No response generated.")
        
        generated_text = result['content'][0]['text']
        if "<resp>" in generated_text and "</resp>" in generated_text:
            clean_text = generated_text.replace("<resp>", "").replace("</resp>", "").strip()
        else:
            clean_text = generated_text.strip()
        
        # Use regex to quote numeric keys (e.g., 1: becomes "1":)
        clean_text = re.sub(r'(\s*)(\d+)(\s*):', r'\1"\2"\3:', clean_text) 
        parsed_json = json.loads(clean_text)
        json_string = json.dumps(parsed_json, indent=2)
        
        pc = Pinecone(api_key=KEY)
        index = pc.Index(IDX_NAME)

        # todo: use this to find he largest doc id to avoid collisions
        max_docID = 0


        for k,v in parsed_json.items():
            # hash of contents salted by random value, in theory there'll be no collisions
            # or if there is it's a very small chance
            d_id = hashlib.sha256(str(v) + str(random.randint(-sys.maxsize-1, sys.maxsize)))
            index.upsert_records(
                records=[
                    {
                        "id": d_id, 
                        "text": str(v), 
                        # can also add:
                        # "category": <cat>,
                    }
                ], 
                namespace=NAMESPACE
            )


        # s3.put_object(
        #     Bucket=bucket_name,
        #     Key='output/result.json',
        #     Body=json_string,
        #     ContentType='application/json'
        # )

        # Print the model's response
        # print("\nGenerated Synthetic Data:")
        # print(clean_text)
    except Exception as e:
        print("An error occurred:", e)
