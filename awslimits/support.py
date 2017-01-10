from awslimitchecker.checker import AwsLimitChecker
import boto3
from boto3.dynamodb.conditions import Key, Attr
from collections import namedtuple
import dateutil.parser
import time
from datetime import datetime, timedelta
from decimal import Decimal

import settings
from dynamo_helpers import create_or_get_table

TICKETS_TABLE_NAME = 'awslimits_tickets'
LIMITS_TABLE_NAME = 'awslimits_limits'
SENT_ALERTS_TABLE_NAME = 'awslimits_sent_alerts'
NAME_SEPARATOR = " :: "
LIMIT_ALERT_PERCENTAGE = settings.LIMIT_ALERT_PERCENTAGE


def dict_to_obj(dict_):
    struct = namedtuple('struct', dict_.keys())
    return struct(**dict_)

def get_boto_resource(resource):
    sts = boto3.client('sts')
    assumed_role = sts.assume_role(RoleArn=settings.ROLE_ARN, RoleSessionName="awslimits")
    credentials = assumed_role['Credentials']
    aws_access_key_id = credentials['AccessKeyId']
    aws_secret_access_key = credentials['SecretAccessKey']
    aws_session_token = credentials['SessionToken']
    return boto3.resource(
        resource,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
        region_name=settings.REGION_NAME
    )

def get_boto_client(client):
    sts = boto3.client('sts')
    assumed_role = sts.assume_role(RoleArn=settings.ROLE_ARN, RoleSessionName="awslimits")
    credentials = assumed_role['Credentials']
    aws_access_key_id = credentials['AccessKeyId']
    aws_secret_access_key = credentials['SecretAccessKey']
    aws_session_token = credentials['SessionToken']
    return boto3.client(
        client,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
        region_name=settings.REGION_NAME
    )


def get_aws_limit_checker():
    return AwsLimitChecker(region=settings.REGION_NAME, account_id=settings.ACCOUNT_ID, account_role=settings.ACCOUNT_ROLE)

def get_tickets_table():
    return create_or_get_table(
        table_name=TICKETS_TABLE_NAME,
        attribute_definitions=[
            {
                'AttributeName': 'display_id',
                'AttributeType': 'N',
            },
        ],
        key_schema=[
            {
                'AttributeName': 'display_id',
                'KeyType': 'HASH'
            },
        ],
    )


def load_tickets():
    table = get_tickets_table()

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
    checker = get_aws_limit_checker()
    for service, service_limits in checker.get_limits(use_ta=settings.PREMIUM_ACCOUNT).items():
        for service_name, service_limit in service_limits.items():
            limit_types.append(NAME_SEPARATOR.join([service, service_name]))
    return sorted(limit_types)

def get_tickets():
    table = get_tickets_table()
    cases = table.scan()['Items']
    cases = sorted(cases, key=lambda case: case['display_id'], reverse=True)
    return cases

def get_ticket(ticket_id):
    table = get_tickets_table()
    ticket = table.query(
        KeyConditionExpression=Key('display_id').eq(ticket_id)
    )['Items'][0]
    return dict_to_obj(ticket)

def get_pending_tickets():
    table = get_tickets_table()
    cases = table.scan(
        FilterExpression=Attr('limit_type').eq('unknown') & Attr('body').ne('N/A')
    )['Items']
    cases = sorted(cases, key=lambda case: case['display_id'], reverse=True)
    return cases


def update_ticket(form):
    table = get_tickets_table()
    limit_type = form.limit_type.data
    table.update_item(
        Key={
            "display_id": form.display_id.data,
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
    service, limit_name = limit_type.split(NAME_SEPARATOR)
    checker = get_aws_limit_checker()
    limits = checker.get_limits(use_ta=settings.PREMIUM_ACCOUNT)
    default_limit = limits[service][limit_name].default_limit

    dynamodb = get_boto_resource('dynamodb')
    tickets_table = get_tickets_table()

    tickets = tickets_table.scan(
        FilterExpression=Attr('limit_type').eq(limit_type)
    )['Items']
    if tickets:
        max_value = max(ticket['limit_value'] for ticket in tickets)
    else:
        max_value = 0

    max_value = max([max_value, default_limit])
    update_dynamodb_limit_value(limit_type, max_value)


def update_dynamodb_limit_value(limit_type, limit_value):
    limits_table = get_limits_table()
    limits_table.update_item(
        Key={
            "limit_name": limit_type,
        },
        AttributeUpdates={
            'current_limit': {
                'Value': limit_value,
                'Action': 'PUT',
            },
    })


def get_limits_table():
    return create_or_get_table(
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


def get_limits():
    limits_table = get_limits_table()
    limits = limits_table.scan()['Items']
    for limit in limits:
        current_limit_float = float(limit['current_limit'])
        limit['percent_used'] = int(float(limit['current_usage']) / current_limit_float * 100) if current_limit_float else None
    return limits


def load_default_limits():
    table = get_limits_table()

    existing_limit_names = [limit['limit_name'] for limit in table.scan()['Items']]

    checker = get_aws_limit_checker()
    checker.find_usage()

    limits = checker.get_limits(use_ta=settings.PREMIUM_ACCOUNT)

    with table.batch_writer() as batch:
        for service, limit_set in limits.items():
            for limit_name, limit in limit_set.items():
                limit_name = NAME_SEPARATOR.join([service, limit_name])
                if limit_name in existing_limit_names:
                    prev_limit = int(table.query(
                        KeyConditionExpression=Key('limit_name').eq(limit_name)
                    )['Items'][0]['current_limit'])
                else:
                    prev_limit = 0

                # In case we now see a higher value in TrustedAdvisor than our previous
                current_limit = max(int(limit.get_limit()), prev_limit)

                usage_limits = limit.get_current_usage()
                if usage_limits:
                    current_usage = max(resource.get_value() for resource in usage_limits)
                else:
                    current_usage = 0
                batch.put_item(
                    Item={
                        'limit_name': limit_name,
                        'service': service,
                        'current_limit': current_limit,
                        'current_usage': int(current_usage),
                    }
                )


def get_tickets_from_aws():
    client = get_boto_client('support')

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


def get_recently_sent_alerts(limits):
    table = create_or_get_table(
        table_name=SENT_ALERTS_TABLE_NAME,
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

    three_days_ago_ts = Decimal((datetime.utcnow() - timedelta(days=3)).strftime('%s'))
    alerts = table.scan(
        FilterExpression=Attr('alert_sent').gt(three_days_ago_ts)
    )['Items']
    return [alert['limit_name'] for alert in alerts]


def get_limits_for_alert():
    limits = get_limits()
    recently_sent_alerts = get_recently_sent_alerts(limits)
    return [x for x in limits if x['percent_used'] > LIMIT_ALERT_PERCENTAGE and x['limit_name'] not in recently_sent_alerts]


def save_sent_alerts(alerts):
    now_timestamp = time.time()
    dynamodb = get_boto_resource('dynamodb')
    table = dynamodb.Table(SENT_ALERTS_TABLE_NAME)
    with table.batch_writer() as batch:
        for alert in alerts:
            table.put_item(
                Item={
                    'limit_name': alert['limit_name'],
                    'percent_used': alert['percent_used'],
                    'alert_sent': Decimal(now_timestamp)
                }
            )


def alert_email_body(limits):
    body = '<ul>We are using {}% or greater of the following services:'.format(LIMIT_ALERT_PERCENTAGE)

    limits = sorted(limits, key=lambda limit: limit['percent_used'], reverse=True)
    for limit in limits:
        body += '<li>{name} - {percent}% (using {usage} of {limit})</li>'.format(
            name=limit['limit_name'],
            percent=limit['percent_used'],
            usage=limit['current_usage'],
            limit=limit['current_limit'],
        )
    body += '</ul>'
    return body
