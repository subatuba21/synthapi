from aws_cdk import (
    # Duration,
    CfnOutput,
    RemovalPolicy,
    Stack,
    # aws_sqs as sqs,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_s3 as s3,
    aws_bedrock as bedrock
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

        agent_role = iam.Role(
            self,
            "BedrockAgentRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com")
        )

        # Add permissions to invoke Lambda
        agent_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["lambda:InvokeFunction"],
                resources=[pinecone.function_arn]
            )
        )

        agent_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeAgent",
                ],
                resources=["*"]
            )
        )

        agent = bedrock.CfnAgent(
            self,
            "SynthAgent",
            agent_name="SynthAgent",
            agent_resource_role_arn=agent_role.role_arn,
            foundation_model="anthropic.claude-3-haiku-20240307-v1:0",  # Claude Haiku
            instruction="You are an agent that fulfills api requests using external data. Here is your workflow:\n1. Receive api url, document namespace, and response format.\n2. Retrieve relevant documents from the external database.\n3. Do additional filtering of the documents.\n4. Transform the documents into the response format.\n5. Your final answer should be pure json. No extraneous text."
        )

        

        # Create Action Group
        action_group = bedrock.CfnAgent.AgentActionGroupProperty(
            action_group_name="PineconeSearch",
            description="A Function Tool that can search a dataset",
            action_group_executor=bedrock.CfnAgent.ActionGroupExecutorProperty(
                lambda_=pinecone.function_arn
            ),
            function_schema=bedrock.CfnAgent.FunctionSchemaProperty(
        functions=[
            bedrock.CfnAgent.FunctionProperty(
                name="search_documents",
                description="Search for documents in Pinecone vector database",
                parameters={
                    "Query-Input": bedrock.CfnAgent.ParameterDetailProperty(
                        type="string",
                        description="The text query to search for",
                        required=True
                    ),
                    "Top-K": bedrock.CfnAgent.ParameterDetailProperty(
                        type="integer",
                        description="Number of top results to return",
                        required=True
                    ),
                    "Namespace": bedrock.CfnAgent.ParameterDetailProperty(
                        type="string",
                        description="Namespace in Pinecone to search in",
                        required=True
                    )
                }
                )
            ]
        ))

            # Add Action Group to Agent
        agent.action_groups = [action_group]

        # Output the Agent ID
        CfnOutput(
            self,
            "AgentId",
            value=agent.attr_agent_id,
            description="Bedrock Agent ID"
        )

        cfn_agent_alias = bedrock.CfnAgentAlias(self, "SynthAgentAlias",
            agent_alias_name="SynthAgentAlias",
            agent_id=agent.ref,
            description="bedrock agent alias to simplify agent invocation"
        )
        cfn_agent_alias.add_dependency(agent) 






