#_*_ coding: UTF-8 _*_

from flask.views import View
import wtforms

import model
import renderers
import custom_fields
import views
import states

TRANSFER_PENDING = states.State(0, 'Pending', ('state-change', 1), ('update',))
TRANSFER_COMPLETE = states.State(1, 'Transferred')
transferStates = [TRANSFER_PENDING, TRANSFER_COMPLETE]

class MoneyForm(wtforms.Form):
    value = wtforms.IntegerField()

class InternalTransferForm(wtforms.Form):
    description = wtforms.TextAreaField()
    amount = wtforms.FormField(MoneyForm, widget=renderers.form_field_widget)
    dest_fund = custom_fields.KeyPropertyField('Destination Fund',
                    validators=[wtforms.validators.InputRequired()],
                    query=model.pont_fund_query())
                    
class InternalTransfer(views.EntityType):
    def __init__(self):
        self.name = 'InternalTransfer'
        self.formClass = InternalTransferForm

    def get_state(self, index):
        return transferStates[index]
        
    def create_entity(self, parent):
        return model.create_transfer(parent)

    def load_entities(self, parent):
        return model.list_transfers(parent)
                        
    def title(self, entity):
        return 'InternalTransfer'

class InternalTransferListView(views.ListView):
    def __init__(self):
        self.entityType = InternalTransfer()
        self.formClass = InternalTransferForm

    def get_fields(self, form):
        state = views.StateField(transferStates)
        return (form._fields['dest_fund'], form._fields['amount'],state)

class InternalTransferView(views.EntityView):
    def __init__(self):
        self.entityType = InternalTransfer()
        self.actions = [(1, 'Transferred')]
        
    def get_fields(self, form):
        state = views.StateField(transferStates)
        creator = views.ReadOnlyKeyField('creator', 'Creator')
        return form._fields.values() + [state, creator]
        
    def get_links(self, entity):
        return []

def add_rules(app):
    app.add_url_rule('/internaltransfer_list/<db_id>', view_func=InternalTransferListView.as_view('view_transfer_list'))
    app.add_url_rule('/internaltransfer/<db_id>/', view_func=InternalTransferView.as_view('view_transfer'))        
    app.add_url_rule('/internaltransfer/<db_id>/menu', view_func=views.MenuView.as_view('handle_transfer_menu'))
