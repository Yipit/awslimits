from flask_wtf import Form
from wtforms import StringField, IntegerField, SelectField

from support import get_limit_types

class TicketForm(Form):
    display_id = IntegerField('Display ID')
    created = IntegerField('Created')
    subject = StringField('Subject')
    status = StringField('Status')
    body = StringField('Body')
    limit_type = SelectField('Limit Type', choices=[(limit, limit) for limit in get_limit_types()])
    limit_value = IntegerField('Limit Value')
