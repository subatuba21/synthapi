from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_lambda as _lambda,
    aws_iam as iam
)
from constructs import Construct
from aws_cdk.aws_lambda_python_alpha import PythonFunction

class FapiStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create the Lambda function
        my_lambda = _lambda.Function(
            self, 
            "MyLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,  # Choose your Python version
            handler="index.handler",            # Format: file.function_name
            code=_lambda.Code.from_asset("fapi/lambda"),  # Directory containing your Lambda code
        )

        pinecone = PythonFunction(
            self, 
            "pinecone_retriever",
            runtime=_lambda.Runtime.PYTHON_3_9,  # Choose your Python version
            handler="handler",            # Format: file.function_name
            entry="fapi/lambda",
            index="retrieve_pinecone.py"  # Directory containing your Lambda code
        )

        pinecone.add_permission(
            "BedrockInvoke",
            principal=iam.ServicePrincipal("bedrock.amazonaws.com"),
            action="lambda:InvokeFunction"
        )
