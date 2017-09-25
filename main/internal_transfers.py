#_*_ coding: UTF-8 _*_

from flask.views import View
import wtforms

import model
import renderers
import custom_fields
import views

class MoneyForm(wtforms.Form):
    value = wtforms.IntegerField()

class InternalTransferForm(wtforms.Form):
    description = wtforms.TextAreaField()
    amount = wtforms.FormField(MoneyForm, widget=renderers.form_field_widget)
    dest_fund = custom_fields.KeyPropertyField('Destination Fund',
                    validators=[wtforms.validators.InputRequired()],
                    query=model.pont_fund_query())

class InternalTransferListView(views.ListView):
    def __init__(self):
        self.kind = 'InternalTransfer'
        self.formClass = InternalTransferForm
        
    def create_entity(self, parent):
        return model.create_transfer(parent)

    def load_entities(self, parent):
        return model.list_transfers(parent)
                
    def get_fields(self, form):
        state = views.ReadOnlyField('state', 'State')
        return (form._fields['dest_fund'], form._fields['amount'],state)

class InternalTransferView(views.EntityView):
    def __init__(self):
        self.formClass = InternalTransferForm
        self.actions = [(1, 'Transferred')]
        
    def get_fields(self, form):
        state = views.ReadOnlyField('state', 'State')
        return form._fields.values() + [state]
    
    def title(self, entity):
        return 'InternalTransfer'
        
    def get_links(self, entity):
        return ""

def add_rules(app):
    app.add_url_rule('/internaltransfer/<db_id>', view_func=InternalTransferListView.as_view('view_transfer_list'))
    app.add_url_rule('/internaltransfer/<db_id>/', view_func=InternalTransferView.as_view('view_transfer'))        
    app.add_url_rule('/internaltransfer/<db_id>/menu', view_func=views.MenuView.as_view('handle_transfer_menu'))
