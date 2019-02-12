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
#states.State('Closed') # 0

state_field = readonly_fields.StateField('Closed', 'Waiting', 'Ready', 'Transferred')

ACTION_CHECKED = model.Action('checked', 'Funds Checked', RoleType.FUND_ADMIN, GRANT_READY, [GRANT_WAITING])
ACTION_TRANSFERRED = model.Action('transferred', 'Transferred', RoleType.PAYMENT_ADMIN, GRANT_TRANSFERED, [GRANT_READY])
ACTION_ACKNOWLEDGED = model.Action('ack', 'Received', RoleType.COMMITTEE_ADMIN, GRANT_CLOSED, [GRANT_TRANSFERED])
ACTION_CANCEL = model.Action('cancel', 'Cancel', RoleType.COMMITTEE_ADMIN, GRANT_CLOSED, [GRANT_WAITING])

class MoneyForm(wtforms.Form):
    currency = custom_fields.SelectField(choices=[('sterling', u'£'), ('ugx', u'Ush')],
                    widget=custom_fields.radio_field_widget)
    value = wtforms.IntegerField(validators=[wtforms.validators.NumberRange(min=100)])

class ExchangeCurrencyField(readonly_fields.ReadOnlyField):
    def __init__(self, label, to_currency):
        super(ExchangeCurrencyField, self).__init__("", label)
        self.to_currency = to_currency

    def render_value(self, entity):
        if (entity.exchange_rate == None):
            return ""
        from_amount = entity.amount
        if from_amount.currency == self.to_currency:
            return unicode(from_amount)
        if self.to_currency == 'ugx':
            value = int(from_amount.value * entity.exchange_rate)
            return unicode(db.Money('ugx', value))
        if self.to_currency == 'sterling':
            value = int(from_amount.value / entity.exchange_rate)
            return unicode(db.Money('sterling', value))
        
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
                ACTION_TRANSFERRED, ACTION_ACKNOWLEDGED, ACTION_CANCEL)

    def create_form(self, request_input, entity):
        return create_grant_form(request_input, entity)

    def get_fields(self, form):
        creator = readonly_fields.ReadOnlyKeyField('creator')
#        transferred_sterling = ExchangeCurrencyField(u'Transferred Amount £', 'sterling')
#        transferred_ugx = ExchangeCurrencyField('Transferred Amount Ush', 'ugx')
        return [state_field, creator] + map(readonly_fields.create_readonly_field, 
                    form._fields.keys(), form._fields.values())

def add_rules(app):
    app.add_url_rule('/grant_list/<db_id>', view_func=GrantListView.as_view('view_grant_list'))
    app.add_url_rule('/grant/<db_id>/', view_func=GrantView.as_view('view_grant'))
