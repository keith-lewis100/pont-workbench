#_*_ coding: UTF-8 _*_

from flask import render_template

from application import app
import db
import data_models
import views
import properties
import renderers

import funds
import projects
import grants
import pledges
import suppliers
import supplier_funds
import internal_transfers
import purchases
import users
import roles
import partners
import foreign_transfer
import committees

audit_fields = [
    properties.DateProperty('timestamp'),
    properties.KeyProperty('entity', title_of=lambda e: e.key.kind()),
    properties.StringProperty('message'),
    properties.KeyProperty('user')
]

@app.route('/')
def home():
    model = data_models.Model(None)
    links = views.view_links(None, 
                ('Committee', 'Show Committees'),
                ('Supplier', 'Show Suppliers'),
                ('User', 'Show Users'))
    audit_list = db.AuditRecord.query().order(-db.AuditRecord.timestamp).iter(limit = 10)
    sub_heading = renderers.sub_heading('Recent Activity')
    table = views.view_entity_list(audit_list, audit_fields, selectable=False)
    content = renderers.render_div(sub_heading, table)
    return render_template('layout.html', title='DashBoard', user=views.view_user_controls(model), links=links,
                           content=content)

projects.add_rules(app)
pledges.add_rules(app)
supplier_funds.add_rules(app)
users.add_rules(app)
partners.add_rules(app)
