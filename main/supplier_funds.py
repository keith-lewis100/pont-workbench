#_*_ coding: UTF-8 _*_

from flask import url_for
import wtforms

import db
import model
import renderers
import custom_fields
import views
from role_types import RoleType

class SupplierFundForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    description = wtforms.TextAreaField()

class SupplierFundModel(model.EntityModel):
    def __init__(self):
        model.EntityModel.__init__(self, 'SupplierFund', RoleType.SUPPLIER_ADMIN)

    def create_entity(self, parent):
        return db.SupplierFund(parent=parent.key)

    def load_entities(self, parent):
        return db.SupplierFund.query(ancestor=parent.key).fetch()
        
    def title(self, entity):
        return 'SupplierFund ' + entity.name

supplier_fund_model = SupplierFundModel()

class SupplierFundListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, supplier_fund_model, SupplierFundForm)

    def get_fields(self, form):
        return [form._fields['name']]

class SupplierFundView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, supplier_fund_model, SupplierFundForm)
        
    def get_fields(self, form):
        return form._fields.values()

    def get_links(self, entity):
        return []
        
def add_rules(app):
    app.add_url_rule('/supplierfund_list/<db_id>', view_func=SupplierFundListView.as_view('view_supplierfund_list'))
    app.add_url_rule('/supplierfund/<db_id>/', view_func=SupplierFundView.as_view('view_supplierfund'))        
