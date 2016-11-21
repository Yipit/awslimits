import os

APP_MODULE="awslimits.server"
APP_OBJECT="app"

SECRET_KEY = "xC^UHBQO&@^Gj^EICCY0"
WTF_CSRF_SECRET_KET = SECRET_KEY

LIMIT_ALERT_PERCENTAGE = int(os.environ.get("LIMIT_ALERT_PERCENTAGE", 90))

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
EMAIL_RECIPIENTS = os.environ.get('EMAIL_RECIPIENTS')
FROM_EMAIL_ADDRESS = os.environ.get('FROM_EMAIL_ADDRESS')
FROM_EMAIL_NAME = os.environ.get('FROM_EMAIL_NAME')

assert SENDGRID_API_KEY, "Need to pass a SendGrid API key. Create one here: https://app.sendgrid.com/settings/api_keys"

