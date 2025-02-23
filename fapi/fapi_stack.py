from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_lambda as _lambda
)
from constructs import Construct

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

        # The code that defines your stack goes here

        # example resource
        # queue = sqs.Queue(
        #     self, "FapiQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )
