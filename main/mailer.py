#_*_ coding: UTF-8 _*_

from flask import render_template
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, HtmlContent

import db

def send_email(subject, content, to_addresses):
    html_content = render_template('email.html', content=content)
    message = Mail(
        from_email='workbench@pont-mbale.org.uk',
        to_emails=map(lambda e: str(e), to_addresses),
        subject=subject,
        html_content=HtmlContent(html_content)
    )
    workbench = db.WorkBench.query().get()
    sg = SendGridAPIClient(workbench.email_api_key)
    response = sg.send(message)
    if response.status_code > 299:
        logging.error('unable to send email subject: %s status: %d' % (subject, response.status_code))
    else:
        logging.info('sent email subject: %s' % subject)
