#_*_ coding: UTF-8 _*_

from flask import url_for
from flask.views import View
import wtforms

import model
import renderers
import custom_fields
import views

class SupplierForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])

class SupplierListView(views.ListView):
    def __init__(self):
        self.kind = 'Supplier'
        self.formClass = SupplierForm
        
    def create_entity(self, parent):
        return model.create_supplier()

    def load_entities(self, parent):
        return model.list_suppliers()
        
    def get_fields(self, form):
        return (form._fields['name'], )

class SupplierView(views.EntityView):
    def __init__(self):
        self.formClass = SupplierForm
        self.actions = []
        
    def get_fields(self, form):
        return form._fields.values()
        
    def title(self, entity):
        return 'Supplier ' + entity.name
                
    def get_links(self, entity):
        funds_url = url_for('view_fund_list', db_id=entity.key.urlsafe())
        showFunds = renderers.render_link('Show Funds', url=funds_url, class_="button")
        return renderers.render_div(showFunds)

def add_rules(app):
    app.add_url_rule('/suppliers', view_func=SupplierListView.as_view('view_supplier_list'))
    app.add_url_rule('/supplier/<db_id>/', view_func=SupplierView.as_view('view_supplier'))
