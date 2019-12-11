import moto
import boto3
from unittest import TestCase
from mock import patch
import os

mock_env = {
    'ROLE_ARN': 'arn:aws:iam::212311232123:role/test',
    'SENDGRID_API_KEY': '1231231231231231231',
    'AWS_ACCESS_KEY_ID': 'awskey',
    'AWS_SECRET_ACCESS_KEY': 'awssecret',
}
with patch.dict(os.environ, mock_env):
    from awslimits.support import create_or_get_table


@moto.mock_dynamodb2
@moto.mock_sts
class TestDynamo(TestCase):
    def test_create_or_get_new_table(self):
        dynamodb = boto3.client('dynamodb', region_name="us-east-1")
        table_name = 'awslimits_limits'
        initial_table_list = dynamodb.list_tables()
        assert table_name not in initial_table_list["TableNames"]
        table = create_or_get_table(
            table_name='awslimits_limits',
            attribute_definitions=[
                {
                    'AttributeName': 'limit_name',
                    'AttributeType': 'S',
                },
            ],
            key_schema=[
                {
                    'AttributeName': 'limit_name',
                    'KeyType': 'HASH'
                },
            ],
        )
        assert table.name == 'awslimits_limits'
        final_table_list = dynamodb.list_tables()
        assert table_name in final_table_list["TableNames"]


    def test_create_or_get_exiting_table(self):
        dynamodb = boto3.client('dynamodb', region_name="us-east-1")
        table_name = 'awslimits_limits1'
        initial_table_list = dynamodb.list_tables()
        assert table_name not in initial_table_list["TableNames"]
        table = create_or_get_table(
            table_name='awslimits_limits1',
            attribute_definitions=[
                {
                    'AttributeName': 'limit_name',
                    'AttributeType': 'S',
                },
            ],
            key_schema=[
                {
                    'AttributeName': 'limit_name',
                    'KeyType': 'HASH'
                },
            ],
        )
        table = create_or_get_table(
            table_name='awslimits_limits1',
            attribute_definitions=[
                {
                    'AttributeName': 'limit_name',
                    'AttributeType': 'S',
                },
            ],
            key_schema=[
                {
                    'AttributeName': 'limit_name',
                    'KeyType': 'HASH'
                },
            ],
        )
        final_table_list = dynamodb.list_tables()
        assert table_name in final_table_list["TableNames"]

    def test_create_or_get_table_exception(self):
        pass

    def test_create_or_get_table_failed(self):
        pass

