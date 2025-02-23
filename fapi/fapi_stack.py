from aws_cdk import (
    # Duration,
    CfnOutput,
    RemovalPolicy,
    Stack,
    # aws_sqs as sqs,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_s3 as s3
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

        init_api_lambda = PythonFunction(
            self,
            "init_api_lambda",
            runtime=_lambda.Runtime.PYTHON_3_9,  # Choose your Python version
            handler="lambda_handler",
            entry="fapi/lambda",
            index="init_api.py"
        )

        bedrock_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "bedrock:InvokeModel",
                "bedrock:InvokeAgent",
                "bedrock:ListAgents",
                "bedrock:ListFoundationModels",
            ],
            resources=["*"]  # You can restrict to specific Bedrock resources/regions if needed
        )

        fn_url = init_api_lambda.add_function_url(
            auth_type=_lambda.FunctionUrlAuthType.NONE,  # Makes it publicly accessible
            cors=_lambda.FunctionUrlCorsOptions(
                allowed_origins=["*"],
                allowed_methods=[_lambda.HttpMethod.ALL],
                allowed_headers=["*"]
            )
        )

        CfnOutput(
            self, 
            "FunctionUrl",
            value=fn_url.url,
            description="URL for the Lambda function"
        )

        # Add the policy to the Lambda's role
        init_api_lambda.add_to_role_policy(bedrock_policy)

        bucket = s3.Bucket(
            self,
            "tempSchemaStorage",
            bucket_name="gt-hacklytics-2025-synthapi",  # Optional: specify a custom name
            versioned=False,  # Enable versioning
            encryption=s3.BucketEncryption.S3_MANAGED,  # Enable encryption
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False
            ),
            removal_policy=RemovalPolicy.RETAIN
        )

        # Add a bucket policy to allow public read access
        bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid="FullPublicAccess",
                effect=iam.Effect.ALLOW,
                principals=[iam.AnyPrincipal()],
                actions=["s3:*"],
                resources=[
                    bucket.bucket_arn,
                    f"{bucket.bucket_arn}/*"
                ]
            )
        )



