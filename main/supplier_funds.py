#_*_ coding: UTF-8 _*_

from flask import url_for
import wtforms

import model
import renderers
import custom_fields
import views

class SupplierFundForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    description = wtforms.TextAreaField()

class SupplierFund(views.EntityType):
    def __init__(self):
        self.name = 'SupplierFund'
        self.formClass = SupplierFundForm

    def get_state(self, index):
        return None
        
    def create_entity(self, parent):
        return model.create_supplier_fund(parent)

    def load_entities(self, parent):
        return model.list_supplier_funds(parent)
        
    def title(self, entity):
        return 'SupplierFund ' + entity.name

class SupplierFundListView(views.ListView):
    def __init__(self):
        self.entityType = SupplierFund()

    def get_fields(self, form):
        return [form._fields['name']]

class SupplierFundView(views.EntityView):
    def __init__(self):
        self.entityType = SupplierFund()
        self.actions = []
        
    def get_fields(self, form):
        return form._fields.values()

    def get_links(self, entity):
        return []
        
def add_rules(app):
    app.add_url_rule('/supplierfund_list/<db_id>', view_func=SupplierFundListView.as_view('view_supplier_fund_list'))
    app.add_url_rule('/supplierfund/<db_id>/', view_func=SupplierFundView.as_view('view_supplier_fund'))        
