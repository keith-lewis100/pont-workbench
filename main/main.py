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
    audit_list = db.AuditRecord.query(db.AuditRecord.parent == None).order(-db.AuditRecord.timestamp).fetch(10)
    sub_heading = renderers.sub_heading('Recent Activity')
    table = views.view_entity_list(audit_list, audit_fields, selectable=False, no_links=False)
    content = renderers.render_div(sub_heading, table)
    return render_template('layout.html', title='DashBoard', user=views.view_user_controls(model), links=links,
                           content=content)
