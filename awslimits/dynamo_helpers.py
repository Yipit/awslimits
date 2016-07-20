import boto3
from botocore.exceptions import ClientError


def create_or_get_table(table_name, attribute_definitions, key_schema):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

    try:
        table = dynamodb.create_table(
            AttributeDefinitions=attribute_definitions,
            TableName=table_name,
            KeySchema=key_schema,
            ProvisionedThroughput={
                'ReadCapacityUnits': 1,
                'WriteCapacityUnits': 1,
            },
        )
    except ClientError as exc:
        if exc.response['Error']['Code'] == 'ResourceInUseException':
            table = dynamodb.Table(table_name)
            return table
        else:
            raise

    table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
    return table
