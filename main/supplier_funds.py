#_*_ coding: UTF-8 _*_

from flask import url_for
import wtforms

import db
import data_models
import renderers
import custom_fields
import readonly_fields
import views
from role_types import RoleType

ACTION_UPDATE = data_models.Action('update', 'Edit', RoleType.SUPPLIER_ADMIN)
ACTION_CREATE = data_models.CreateAction(RoleType.SUPPLIER_ADMIN)

class SupplierFundForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    description = wtforms.TextAreaField()

class SupplierFundListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, 'SupplierFund', ACTION_CREATE)

    def load_entities(self, parent):
        return db.SupplierFund.query(ancestor=parent.key).fetch()

    def create_entity(self, parent):
        return db.SupplierFund(parent=parent.key)

    def create_form(self, request_input, entity):
        return SupplierFundForm(request_input, obj=entity)

    def get_fields(self, form):
        return [readonly_fields.ReadOnlyField('name')]

class SupplierFundView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, ACTION_UPDATE, 1)
        
    def title(self, entity):
        return 'SupplierFund ' + entity.name

    def create_form(self, request_input, entity):
        return SupplierFundForm(request_input, obj=entity)
        
    def get_fields(self, form):
        return map(readonly_fields.create_readonly_field, form._fields.keys(), form._fields.values())

    def get_links(self, entity):
        projects_url = url_for('view_project_list', db_id=entity.key.urlsafe())
        showProjects = renderers.render_link('Show Projects', projects_url, class_="button")
        return [showProjects]

def add_rules(app):
    app.add_url_rule('/supplierfund_list/<db_id>', view_func=SupplierFundListView.as_view('view_supplierfund_list'))
    app.add_url_rule('/supplierfund/<db_id>/', view_func=SupplierFundView.as_view('view_supplierfund'))        
