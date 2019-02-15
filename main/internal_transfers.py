#_*_ coding: UTF-8 _*_

from flask.views import View
import wtforms

import db
import model
import renderers
import custom_fields
import readonly_fields
import views
from role_types import RoleType

TRANSFER_PENDING = 1
TRANSFER_COMPLETE = 0
state_field = readonly_fields.StateField('Transferred', 'Pending')

ACTION_TRANSFERRED = model.StateAction('transferred', 'Transferred', RoleType.FUND_ADMIN, 
                            TRANSFER_COMPLETE, [TRANSFER_PENDING])

class MoneyForm(wtforms.Form):
    value = wtforms.IntegerField()

class InternalTransferForm(wtforms.Form):
    amount = wtforms.FormField(MoneyForm, widget=custom_fields.form_field_widget)
    dest_fund = custom_fields.SelectField('Destination Fund', coerce=model.create_key, 
                    validators=[wtforms.validators.InputRequired()])
    description = wtforms.TextAreaField()

def create_transfer_form(request_fields, entity):
    form = InternalTransferForm(request_fields, obj=entity)
    fund_list = db.Fund.query().fetch()
    custom_fields.set_field_choices(form.dest_fund, fund_list)
    return form

class InternalTransferModel(model.EntityModel):
    def __init__(self):
        model.EntityModel.__init__(self, 'InternalTransfer', RoleType.COMMITTEE_ADMIN, TRANSFER_PENDING)
        
    def create_entity(self, parent):
        return db.InternalTransfer(parent=parent.key)

    def load_entities(self, parent):
        return db.InternalTransfer.query(ancestor=parent.key).fetch()
                        
    def title(self, entity):
        dest_name = entity.dest_fund.get().name if entity.dest_fund != None else ""
        return 'InternalTransfer to ' + dest_name

transfer_model = InternalTransferModel()

class InternalTransferListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, transfer_model)

    def create_form(self, request_input, entity):
        return create_transfer_form(request_input, entity)

    def get_fields(self, form):
        return (readonly_fields.create_readonly_field('dest_fund', form.dest_fund),
                readonly_fields.ReadOnlyField('amount'), state_field)

class InternalTransferView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, transfer_model)

    def create_form(self, request_input, entity):
        return create_transfer_form(request_input, entity)

    def get_fields(self, form):
        creator = readonly_fields.ReadOnlyKeyField('creator', 'Creator')
        return [state_field, creator] + map(readonly_fields.create_readonly_field, 
                       form._fields.keys(), form._fields.values())

    def get_links(self, entity):
        return []

def add_rules(app):
    app.add_url_rule('/internaltransfer_list/<db_id>', view_func=InternalTransferListView.as_view('view_internaltransfer_list'))
    app.add_url_rule('/internaltransfer/<db_id>/', view_func=InternalTransferView.as_view('view_internaltransfer'))        
