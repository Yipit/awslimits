from awslimitchecker.checker import AwsLimitChecker
import boto3
from boto3.dynamodb.conditions import Key, Attr
from collections import namedtuple
import dateutil.parser

from dynamo_helpers import create_or_get_table

TICKETS_TABLE_NAME = 'awslimits_tickets'
LIMITS_TABLE_NAME = 'awslimits_limits'
NAME_SEPARATOR = " :: "


def dict_to_obj(dict_):
    struct = namedtuple('struct', dict_.keys())
    return struct(**dict_)

def load_tickets():
    table = create_or_get_table(
        table_name=TICKETS_TABLE_NAME,
        attribute_definitions=[
            {
                'AttributeName': 'display_id',
                'AttributeType': 'N',
            },
            {
                'AttributeName': 'created',
                'AttributeType': 'N',
            },
        ],
        key_schema=[
            {
                'AttributeName': 'display_id',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'created',
                'KeyType': 'RANGE'
            },
        ],
    )

    current_ticket_ids = set(ticket['display_id'] for ticket in get_tickets())
    with table.batch_writer() as batch:
        for ticket in get_tickets_from_aws():
            ticket_id = int(ticket['displayId'])
            if ticket_id not in current_ticket_ids:
                separator = '==================================================='
                aggregated_body = separator.join(communication['body'] for communication in reversed(ticket['recentCommunications']['communications']))
                if not aggregated_body:
                    aggregated_body = 'N/A'
                batch.put_item(
                    Item={
                        'display_id': ticket_id,
                        'case_id': ticket['caseId'],
                        'created': int(dateutil.parser.parse(ticket['timeCreated']).strftime("%s")),
                        'subject': ticket['subject'],
                        'body': aggregated_body,
                        'status': ticket['status'],
                        'limit_type': 'unknown',
                        'limit_value': 0,
                    }
                )

def get_limit_types():
    limit_types = []
    checker = AwsLimitChecker(region='us-east-1')
    for service, service_limits in checker.get_limits(use_ta=False).items():
        for service_name, service_limit in service_limits.items():
            limit_types.append(NAME_SEPARATOR.join([service, service_name]))
    return sorted(limit_types)

def get_tickets():
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table(TICKETS_TABLE_NAME)
    cases = table.scan()['Items']
    cases = sorted(cases, key=lambda case: case['display_id'], reverse=True)
    return cases

def get_ticket(ticket_id):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table(TICKETS_TABLE_NAME)
    ticket = table.query(
        KeyConditionExpression=Key('display_id').eq(ticket_id)
    )['Items'][0]
    return dict_to_obj(ticket)

def get_pending_tickets():
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table(TICKETS_TABLE_NAME)
    cases = table.scan(
        FilterExpression=Attr('limit_type').eq('unknown')
    )['Items']
    cases = sorted(cases, key=lambda case: case['display_id'], reverse=True)
    return cases


def update_ticket(form):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table(TICKETS_TABLE_NAME)
    limit_type = form.limit_type.data
    table.update_item(
        Key={
            "display_id": form.display_id.data,
            "created": form.created.data,
        },
        AttributeUpdates={
            'limit_type': {
                'Value': limit_type,
                'Action': 'PUT',
            },
            'limit_value': {
                'Value': form.limit_value.data,
                'Action': 'PUT',
            },
    })
    update_limit_value(limit_type)

def update_limit_value(limit_type):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    limits_table = dynamodb.Table(LIMITS_TABLE_NAME)

    service, limit_name = limit_type.split(NAME_SEPARATOR)
    checker = AwsLimitChecker(region='us-east-1')
    limits = checker.get_limits()
    default_limit = limits[service][limit_name].default_limit

    tickets_table = dynamodb.Table(TICKETS_TABLE_NAME)

    tickets = tickets_table.scan(
        FilterExpression=Attr('limit_type').eq(limit_type)
    )['Items']
    if tickets:
        max_value = max(ticket['limit_value'] for ticket in tickets)
    else:
        max_value = 0

    max_value = max([max_value, default_limit])

    limits_table.update_item(
        Key={
            "limit_name": limit_type,
        },
        AttributeUpdates={
            'current_limit': {
                'Value': max_value,
                'Action': 'PUT',
            },
    })

def get_limits():
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    limits_table = dynamodb.Table(LIMITS_TABLE_NAME)
    limits = limits_table.scan()['Items']
    for limit in limits:
        limit['percent_used'] =  str(int(float(limit['current_usage']) / float(limit['current_limit']) * 100)) + '%'
    return limits


def load_default_limits():
    table = create_or_get_table(
        table_name=LIMITS_TABLE_NAME,
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

    existing_limit_names = [limit['limit_name'] for limit in table.scan()['Items']]

    checker = AwsLimitChecker(region='us-east-1')
    checker.find_usage()

    limits = checker.get_limits()
    with table.batch_writer() as batch:
        for service, limit_set in limits.items():
            for limit_name, limit in limit_set.items():
                limit_name = NAME_SEPARATOR.join([service, limit_name])

                usage_limits = limit.get_current_usage()
                if usage_limits:
                    current_usage = max(resource.get_value() for resource in usage_limits)
                else:
                    current_usage = 0
                batch.put_item(
                    Item={
                        'limit_name': limit_name,
                        'service': service,
                        'current_limit': int(limit.get_limit()),
                        'current_usage': int(current_usage),
                    }
                )


def get_tickets_from_aws():
    client = boto3.client('support', region_name='us-east-1')

    cases = []
    next_token = None
    while True:
        if next_token:
            results = client.describe_cases(includeResolvedCases=True, nextToken=next_token)
        else:
            results = client.describe_cases(includeResolvedCases=True)
        for case in results['cases']:
            if case['serviceCode'] == 'service-limit-increase':
                cases.append(case)
        if 'nextToken' in results:
            next_token = results['nextToken']
        else:
            break

    return cases
