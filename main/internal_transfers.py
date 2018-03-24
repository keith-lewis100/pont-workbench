#_*_ coding: UTF-8 _*_

from flask.views import View
import wtforms

import db
import model
import renderers
import custom_fields
import views
import states
from role_types import RoleType

TRANSFER_PENDING = states.State('Pending', True, True, {1: RoleType.FUND_ADMIN}) # 0
TRANSFER_COMPLETE = states.State('Transferred') # 1
transferStates = [TRANSFER_PENDING, TRANSFER_COMPLETE]

class MoneyForm(wtforms.Form):
    value = wtforms.IntegerField()

class InternalTransferForm(wtforms.Form):
    description = wtforms.TextAreaField()
    amount = wtforms.FormField(MoneyForm, widget=renderers.form_field_widget)
    dest_fund = custom_fields.KeyPropertyField('Destination Fund',
                    validators=[wtforms.validators.InputRequired()],
                    query=db.Fund.query())

class InternalTransferModel(model.EntityModel):
    def __init__(self):
        model.EntityModel.__init__(self, 'InternalTransfer', RoleType.COMMITTEE_ADMIN, None, transferStates)
        
    def create_entity(self, parent):
        return db.InternalTransfer(parent=parent.key)

    def load_entities(self, parent):
        return db.InternalTransfer.query(ancestor=parent.key).fetch()
                        
    def title(self, entity):
        return 'InternalTransfer ' + str(entity.key.id())

transfer_model = InternalTransferModel()

class InternalTransferListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, transfer_model, InternalTransferForm)

    def get_fields(self, form):
        id = views.IdField()
        state = views.StateField(transferStates)
        return (id, form._fields['dest_fund'], form._fields['amount'],state)

class InternalTransferView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, transfer_model, InternalTransferForm, (1, 'Transferred'))
        
    def get_fields(self, form):
        state = views.StateField(transferStates)
        creator = views.ReadOnlyKeyField('creator', 'Creator')
        return form._fields.values() + [state, creator]
        
    def get_links(self, entity):
        return []

def add_rules(app):
    app.add_url_rule('/internaltransfer_list/<db_id>', view_func=InternalTransferListView.as_view('view_internaltransfer_list'))
    app.add_url_rule('/internaltransfer/<db_id>/', view_func=InternalTransferView.as_view('view_internaltransfer'))        
    app.add_url_rule('/internaltransfer/<db_id>/menu', view_func=views.MenuView.as_view('handle_transfer_menu', transfer_model))
