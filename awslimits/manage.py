import os
import sendgrid
from flask_script import Manager

from server import app
from support import get_limits_for_alert, alert_email_body

manager = Manager(app)


@manager.command
def send_alerts():
	limits_for_alert = get_limits_for_alert()
	if limits_for_alert:
		content = alert_email_body(limits_for_alert)
		email_recipients = [{'email': email} for email in os.environ.get('EMAIL_RECIPIENTS').split(',')]
		sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY'))
		data = {
			'content': [
				{
					'type': 'text/html',
					'value': '<html>{}</html>'.format(content)
				}
			],
			'from': {
					'email': os.environ.get('FROM_EMAIL_ADDRESS'),
					'name': os.environ.get('FROM_EMAIL_NAME')
				},
			'personalizations': [
				{
					'to': email_recipients
				}
			],
			'subject': "AWS Limit Alerts for {}".format(os.environ.get('ROLE_NAME')),
		}
		sg.client.mail.send.post(request_body=data)


if __name__ == "__main__":
    manager.run()