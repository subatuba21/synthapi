def handler(event, context):
    print("Request:", event)
    
    return {
        'statusCode': 200,
        'body': 'Hello from Lambda!'
    }