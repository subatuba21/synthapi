from pinecone import Pinecone
import json
import jsonpickle

top_k_key = 'Top-K'
query_input_key = 'Query-Input'
name_space_key = 'Namespace'


def search_by_text(query_text, index_name, top_k=10, namespace="", api_key="your_api_key"):
   pc = Pinecone(api_key=api_key)
   index = pc.Index(index_name)
   
   search_results = index.search_records(
       query={
          "inputs": {"text": query_text}, 
          "top_k": top_k
       },
       namespace=namespace
   )
   
   return search_results


def handler(event, context):
    agent = event['agent']
    actionGroup = event['actionGroup']
    function = event['function']
    parameters = event.get('parameters', [])

    print(event, context)

    # Initialize params as None to check if they're set
    top_k = None
    query_input = None
    name_space = None

    # Parse parameters
    for param in parameters:
        if param.get('name') == 'Top-K':
            top_k = int(param.get('value'))
        elif param.get('name') == 'Query-Input':
            query_input = param.get('value')
        elif param.get('name') == 'Namespace':
            name_space = param.get('value')

    # Validate all required parameters
    missing_params = []
    if top_k is None:
        missing_params.append('Top-K')
    if query_input is None:
        missing_params.append('Query-Input')
    if name_space is None:
        missing_params.append('Namespace')

    if missing_params:
        raise ValueError(f"Missing required parameters: {', '.join(missing_params)}")


    results = search_by_text(
#    query_vector=query_vec, 
        query_text=query_input,
        index_name="quickstart2",
        top_k=top_k,
        namespace=name_space,
        api_key="pcsk_5fjTMD_94yGbMH2Ujw2d3CEqfyvByLqeswYEP4LGLePfYQzfsiEKK1RoY2Z7UX9qnQ3sq3"
    )

    # print(results, results.result, results.result.hits)



    # Execute your business logic here. For more information, refer to: https://docs.aws.amazon.com/bedrock/latest/userguide/agents-lambda.html
    responseBody =  {
        "TEXT": {
            "body": json.dumps(list(map(lambda hit: hit.fields, results.result.hits)))
        }
    }

    action_response = {
        'actionGroup': actionGroup,
        'function': function,
        'functionResponse': {
            'responseBody': responseBody
        }

    }

    dummy_function_response = {'response': action_response, 'messageVersion': event['messageVersion']}

    return dummy_function_response
