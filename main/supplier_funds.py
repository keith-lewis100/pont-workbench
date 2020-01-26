#_*_ coding: UTF-8 _*_

import wtforms

import db
import properties
import views
from role_types import RoleType

ACTION_UPDATE = views.update_action(RoleType.SUPPLIER_ADMIN)
ACTION_CREATE = views.create_action(RoleType.SUPPLIER_ADMIN)

class SupplierFundForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    description = wtforms.TextAreaField()
    partner_required = wtforms.BooleanField('Project Partner Required')

class SupplierFundListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, 'SupplierFund', ACTION_CREATE)

    def load_entities(self, parent):
        return db.SupplierFund.query(ancestor=parent.key).order(db.SupplierFund.name).fetch()

    def create_entity(self, parent):
        return db.SupplierFund(parent=parent.key)

    def create_form(self, request_input, entity):
        return SupplierFundForm(request_input, obj=entity)

    def get_fields(self, form):
        return [properties.StringProperty('name')]

class SupplierFundView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, ACTION_UPDATE, 1)
        
    def title(self, entity):
        return 'SupplierFund ' + entity.name

    def create_form(self, request_input, entity):
        if request_input:
          return SupplierFundForm(request_input)
        else:
          return SupplierFundForm(obj=entity)
        
    def get_fields(self, form):
        return map(properties.create_readonly_field, form._fields.keys(), form._fields.values())

def add_rules(app):
    app.add_url_rule('/supplierfund_list/<db_id>', view_func=SupplierFundListView.as_view('view_supplierfund_list'))
    app.add_url_rule('/supplierfund/<db_id>/', view_func=SupplierFundView.as_view('view_supplierfund'))        
