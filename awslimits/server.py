import datetime
from flask import Flask, render_template, request, redirect, url_for, Response

from awslimits.forms import TicketForm
from awslimits.support import get_tickets, get_ticket, update_ticket, get_limits, get_pending_tickets, update_dynamodb_limit_value

app = Flask(__name__)
app.debug = True
app.config.from_object("awslimits.settings")


@app.route("/")
def limits():
    sort_param = request.args.get('sort')
    limits = get_limits()
    if sort_param == 'alpha':
        limits = sorted(limits, key=lambda limit: limit['limit_name'])
    else:
        limits = sorted(limits, key=lambda limit: limit['percent_used'], reverse=True)
    return render_template('limits.html', limits=limits)


@app.route("/cases")
def tickets():
    tickets = get_tickets()
    return render_template("cases.html", tickets=tickets)


@app.route("/pending-cases")
def pending_tickets():
    tickets = get_pending_tickets()
    return render_template("cases.html", tickets=tickets)


@app.route("/cases/<ticket_id>", methods=['GET', 'POST'])
def individual_ticket(ticket_id):
    ticket = get_ticket(int(ticket_id))
    form = TicketForm(request.form, ticket)

    if request.method == 'POST' and form.validate():
        update_ticket(form)
        return redirect(url_for('pending_tickets'))

    return render_template("ticket.html", form=form)


@app.route("/limits/<limit_type>", methods=['POST'])
def update_limit(limit_type):
    limit_value = request.form['limit_value']
    update_dynamodb_limit_value(limit_type, limit_value)
    return redirect(url_for('limits'))


@app.route("/healthcheck")
def healthcheck():
    """Healthcheck endpoint for confirming server is responding."""

    return Response('it works', status=200)


@app.context_processor
def inject_pending_ticket_count():
    tickets = get_pending_tickets()
    return dict(pending_ticket_count=len(tickets))


@app.template_filter('convert_epoch_time')
def convert_epoch_time(datetime_):
    return datetime.datetime.fromtimestamp(datetime_)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
