#_*_ coding: UTF-8 _*_

from flask import render_template

from application import app
import db
import data_models
import views
import properties
import renderers
import role_types

from page import *

audit_fields = [
    properties.DateProperty('timestamp'),
    properties.StringProperty(lambda e: e.entity.kind(), 'EntityType'),
    properties.KeyProperty('entity'),
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
    audit_list = [ a for a in audit_list if a.parent is None ]
    sub_heading = renderers.sub_heading('Recent Activity')
    table = views.view_entity_list(audit_list, audit_fields, selectable=False, no_links=False)
    content = renderers.render_div(sub_heading, table)
    return render_template('layout.html', title='DashBoard', user=views.view_user_controls(model), links=links,
                           content=content)

pledges.add_rules(app)
supplier_funds.add_rules(app)
users.add_rules(app)
partners.add_rules(app)
