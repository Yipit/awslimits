import os
import sendgrid
from flask_script import Manager

import settings
from server import app
from support import get_limits_for_alert, alert_email_body, save_sent_alerts

manager = Manager(app)


@manager.command
def send_alerts():
	limits_for_alert = get_limits_for_alert()
	if limits_for_alert:
		content = alert_email_body(limits_for_alert)
		recipients = [{'email': email} for email in settings.EMAIL_RECIPIENTS.split(',')]
		sg = sendgrid.SendGridAPIClient(apikey=settings.SENDGRID_API_KEY)
		data = {
			'content': [
				{
					'type': 'text/html',
					'value': '<html>{}</html>'.format(content)
				}
			],
			'from': {
					'email': settings.FROM_EMAIL_ADDRESS,
					'name': settings.FROM_EMAIL_NAME
				},
			'personalizations': [
				{
					'to': recipients
				}
			],
			'subject': "AWS Limit Alerts for {}".format(os.environ.get('ROLE_NAME')),
		}
		sg.client.mail.send.post(request_body=data)
		save_sent_alerts(limits_for_alert)


if __name__ == "__main__":
    manager.run()
