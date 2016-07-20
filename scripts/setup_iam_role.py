from botocore.exceptions import ClientError
import boto3
import json
import sys

POLICY_DOCUMENT = {
    "Statement":[
        {
            "Action": ["dynamodb:Scan", "dynamodb:Query"],
            "Effect": "Allow",
            "Resource": "*"
        },



    {
        "Action":[
            "ec2:Describe*"
        ],
            "Effect":"Allow",
            "Resource":"*"
        },
        {
        "Action":["rds:Describe*"],
        "Effect":"Allow",
        "Resource":"*"
        },
        {
        "Action":["s3:Get*",
        "s3:List*"
        ],
        "Effect":"Allow",
        "Resource":"*"
        },
        {
        "Action":["sdb:GetAttributes",
        "sdb:List*",
        "sdb:Select*"
        ],
        "Effect":"Allow",
        "Resource":"*"
        },
        {
        "Action":["sns:Get*",
        "sns:List*"
        ],
        "Effect":"Allow",
        "Resource":"*"
        },
        {
        "Action":["sqs:ListQueues",
        "sqs:GetQueueAttributes",
        "sqs:ReceiveMessage"
        ],
        "Effect":"Allow",
        "Resource":"*"
        },
        {
        "Action":["autoscaling:Describe*"
        ],
        "Effect":"Allow",
        "Resource":"*"
        },
        {
        "Action":["elasticloadbalancing:Describe*"
        ],
        "Effect":"Allow",
        "Resource":"*"
        },
        {
        "Action":["cloudwatch:Describe*",
        "cloudwatch:List*",
        "cloudwatch:Get*"
        ],
        "Effect":"Allow",
        "Resource":"*"
        },
        {
        "Action":[
        "iam:Get*",
        "iam:List*"
        ],
        "Effect":"Allow",
        "Resource":"*"
        }
    ]
}

LAMBDA_ASSUME_POLICY = {
  "Version": "2012-10-17",
  "Statement":[{
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
  },{
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "apigateway.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
  }
  ]
}

client = boto3.client('iam')

ROLE_NAME = 'awslimits'
try:
    client.create_role(
        RoleName=ROLE_NAME,
        AssumeRolePolicyDocument=json.dumps(LAMBDA_ASSUME_POLICY),
    )
except ClientError as exc:
    if exc.response['Error']['Code'] != 'EntityAlreadyExists':
        raise

client.put_role_policy(
    RoleName=ROLE_NAME,
    PolicyName=ROLE_NAME,
    PolicyDocument=json.dumps(POLICY_DOCUMENT),
)

env, settings = sys.argv[1:]
settings = json.loads(open(settings).read())[env]
function_name = "-".join([settings['project_name'], env])

lambda_client = boto3.client("lambda", region_name='us-east-1')
try:
    lambda_client.delete_function(
        FunctionName=function_name,
    )
except ClientError as exc:
    if exc.response['Error']['Code'] != 'ResourceNotFoundException':
        raise


apigateway_client = boto3.client("apigateway", region_name='us-east-1')

apis = apigateway_client.get_rest_apis()['items']
matching_api_ids = [api['id'] for api in apis if api['name'] == function_name]
for matching_api_id in matching_api_ids:
    response = apigateway_client.delete_rest_api(
        restApiId=matching_api_id
    )
