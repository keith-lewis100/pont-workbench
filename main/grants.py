#_*_ coding: UTF-8 _*_

from flask.views import View
from flask import request
import wtforms
import wtforms.widgets.html5 as widgets
from datetime import date, timedelta
import db
import model
import renderers
import views
import custom_fields
import readonly_fields
from role_types import RoleType

GRANT_WAITING = 1
GRANT_READY = 2
GRANT_TRANSFERED = 3
GRANT_CLOSED = 0

state_field = readonly_fields.StateField('Closed', 'Waiting', 'Ready', 'Transferred')

class CheckedAction(model.StateAction):
    def apply_to(self, entity, user=None):
        entity.state_index = GRANT_READY
        entity.transfer = None    
        entity.put()

ACTION_CHECKED = CheckedAction('checked', 'Funds Checked', RoleType.FUND_ADMIN, GRANT_READY, [GRANT_WAITING])
ACTION_ACKNOWLEDGED = model.StateAction('ack', 'Received', RoleType.COMMITTEE_ADMIN, GRANT_CLOSED, [GRANT_TRANSFERED])
ACTION_CANCEL = model.StateAction('cancel', 'Cancel', RoleType.COMMITTEE_ADMIN, GRANT_CLOSED, [GRANT_WAITING])

class MoneyForm(wtforms.Form):
    currency = custom_fields.SelectField(choices=[('sterling', u'£'), ('ugx', u'Ush')],
                    widget=custom_fields.radio_field_widget)
    value = wtforms.IntegerField(validators=[wtforms.validators.NumberRange(min=100)])

class ExchangeCurrencyField(readonly_fields.ReadOnlyField):
    def __init__(self, name):
        super(ExchangeCurrencyField, self).__init__(name)

    def render_value(self, grant):
        if getattr(grant, 'transfer', None) is None:
            return ""
        transfer = grant.transfer.get()
        if transfer.exchange_rate is None:
            return ""
        requested_amount = grant.amount.value
        if grant.amount.currency == 'sterling':
            sterling = requested_amount
            shillings = int(requested_amount * transfer.exchange_rate)
        if grant.amount.currency == 'ugx':
            sterling = int(requested_amount / transfer.exchange_rate)
            shillings = requested_amount
        return u"£{:,}".format(sterling) + "/" + u"{:,}".format(shillings) + ' Ush'

class GrantForm(wtforms.Form):
    amount = wtforms.FormField(MoneyForm, label='Requested Amount', widget=custom_fields.form_field_widget)
    project = custom_fields.SelectField(coerce=model.create_key, validators=[wtforms.validators.InputRequired()])
    target_date = wtforms.DateField(widget=widgets.MonthInput(), format='%Y-%m',
                                validators=[wtforms.validators.InputRequired()])
    description = wtforms.TextAreaField()

def create_grant_form(request_input, entity):
    form = GrantForm(request_input, obj=entity)
    fund = entity.key.parent().get()
    project_list = db.Project.query(db.Project.committee == fund.committee).fetch()
    custom_fields.set_field_choices(form._fields['project'], project_list)
    return form

class GrantModel(model.EntityModel):
    def __init__(self):
        model.EntityModel.__init__(self, 'Grant', RoleType.COMMITTEE_ADMIN, GRANT_WAITING)
        
    def create_entity(self, parent):
        entity = db.Grant(parent=parent.key)
        entity.target_date = date.today() + timedelta(30)
        return entity

    def load_entities(self, parent):
        return db.Grant.query(ancestor=parent.key).fetch()
        
    def title(self, entity):
        return 'Grant on ' + str(entity.target_date)

grant_model = GrantModel()

class GrantListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, grant_model)

    def create_form(self, request_input, entity):
        return create_grant_form(request_input, entity)

    def get_fields(self, form):
        return (readonly_fields.ReadOnlyKeyField('project'),
                readonly_fields.ReadOnlyField('amount'), state_field)

class GrantView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, grant_model, ACTION_CHECKED,
                ACTION_ACKNOWLEDGED, ACTION_CANCEL)

    def create_form(self, request_input, entity):
        return create_grant_form(request_input, entity)

    def get_fields(self, form):
        creator = readonly_fields.ReadOnlyKeyField('creator')
        transferred = ExchangeCurrencyField('transferred_amount')
        return [state_field, creator, transferred] + map(readonly_fields.create_readonly_field, 
                    form._fields.keys(), form._fields.values())

def add_rules(app):
    app.add_url_rule('/grant_list/<db_id>', view_func=GrantListView.as_view('view_grant_list'))
    app.add_url_rule('/grant/<db_id>/', view_func=GrantView.as_view('view_grant'))
