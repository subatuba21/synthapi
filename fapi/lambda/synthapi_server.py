import boto3
import json
import os

def handler(event, context):
    
    url_split = event["rawPath"].split("/")
    
    print(event["rawPath"], url_split, event)
    if len(url_split) < 1:
        print("here")
        return False
    
    api_name = url_split[1]
    api_path = "/".join(url_split[2:])

    s3 = boto3.client('s3')
    bucket_name = 'gt-hacklytics-2025-synthapi'

    openapi_file_name = f'schemas/{api_name}.json'

    print(openapi_file_name)

    response = s3.get_object(Bucket=bucket_name, Key=openapi_file_name)

    if not response:
        print("here2", openapi_file_name)
        return False
    
    file_content = response['Body'].read().decode('utf-8')
    
    json_data = json.loads(file_content)

    print(json_data)


    client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

    agent_id = os.environ['agent_id']
    agent_alias_id = os.environ['agent_alias_id']

    response = client.invoke_agent(
        agentId=agent_id,
        agentAliasId=agent_alias_id,
        inputText='api request: "https://fakeapi.com/restaurants?type=pizza", namespace: "records", response_format: { "name": string, "address": string }',
        sessionId=str(math.random() * 1000)
    )

    print(response)








