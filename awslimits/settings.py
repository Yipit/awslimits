import os
import re

APP_MODULE="awslimits.server"
APP_OBJECT="app"

SECRET_KEY = "xC^UHBQO&@^Gj^EICCY0"
WTF_CSRF_SECRET_KET = SECRET_KEY

ROLE_ARN = os.environ.get("ROLE_ARN")
ACCOUNT_ID = re.findall('\d+', ROLE_ARN)[0]
ACCOUNT_ROLE = ROLE_ARN.split('/')[-1]
REGION_NAME = os.environ.get("REGION_NAME", "us-east-1")
PREMIUM_ACCOUNT = int(os.environ.get("PREMIUM_ACCOUNT", 1))

assert ROLE_ARN, "Need to pass a role ARN"

LIMIT_ALERT_PERCENTAGE = int(os.environ.get("LIMIT_ALERT_PERCENTAGE", 90))

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
EMAIL_RECIPIENTS = os.environ.get('EMAIL_RECIPIENTS')
FROM_EMAIL_ADDRESS = os.environ.get('FROM_EMAIL_ADDRESS', 'awslimits@alerts.com')
FROM_EMAIL_NAME = os.environ.get('FROM_EMAIL_NAME')

assert SENDGRID_API_KEY, "Need to pass a SendGrid API key. Create one here: https://app.sendgrid.com/settings/api_keys"

# list of limit names to snooze. Need split because of ::
# ex: SNOOZE='S3 :: Buckets,VPC :: Subnets per VPC'
SNOOZE = os.environ.get("SNOOZE", '').replace('\'', '').replace('"', '')

