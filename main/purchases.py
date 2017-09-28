#_*_ coding: UTF-8 _*_

from flask.views import View
import wtforms

import model
import renderers
import views

class MoneyForm(wtforms.Form):
    currency = wtforms.SelectField(choices=[('sterling', u'£'), ('ugx', u'Ush')],
                    widget=renderers.radio_field_widget)
    value = wtforms.IntegerField(validators=[wtforms.validators.NumberRange(min=100)])

class PurchaseForm(wtforms.Form):
    description = wtforms.TextAreaField()
    amount = wtforms.FormField(MoneyForm, widget=renderers.form_field_widget)

class PurchaseListView(views.ListView):
    def __init__(self):
        self.kind = 'Purchase'
        self.formClass = PurchaseForm
        
    def create_entity(self, parent):
        return model.create_purchase(parent)

    def load_entities(self, parent):
        return model.list_purchases(parent)
        
    def get_fields(self, form):
        po_number = views.ReadOnlyField('po_number', 'PO number')
        state = views.ReadOnlyField('state', 'State')
        return (form._fields['amount'], po_number, state)

class PurchaseView(views.EntityView):
    def __init__(self):
        self.formClass = PurchaseForm
        self.actions = [(2, 'Approve'), (3, 'Ordered'), (4, 'Fulfilled'), (5, 'Close')]
        
    def get_fields(self, form):
        po_number = views.ReadOnlyField('po_number', 'PO number')
        state = views.ReadOnlyField('state', 'State')
        creator = views.ReadOnlyKeyField('creator', 'Creator')
        return form._fields.values() + [po_number, state, creator]
        
    def title(self, entity):
        return "Purchase"

    def get_links(self, entity):
        return ""

def add_rules(app):
    app.add_url_rule('/purchase_list/<db_id>', view_func=PurchaseListView.as_view('view_purchase_list'))
    app.add_url_rule('/purchase/<db_id>/', view_func=PurchaseView.as_view('view_purchase'))
    app.add_url_rule('/purchase/<db_id>/menu', view_func=views.MenuView.as_view('handle_purchase_menu'))
