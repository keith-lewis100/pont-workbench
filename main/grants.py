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
from role_types import RoleType
from projects import project_model

GRANT_WAITING = 1
#states.State('Waiting', True, {'checked': RoleType.FUND_ADMIN, 'cancel': RoleType.COMMITTEE_ADMIN})
GRANT_READY = 2
#states.State('Ready', False, {'exchange': RoleType.PAYMENT_ADMIN}) # 2
GRANT_CURRENCY_REQUESTED = 3
#states.State('Exchanging Currency', False, {'transferred': RoleType.PAYMENT_ADMIN}) # 3
GRANT_TRANSFERED = 4
#states.State('Transferred', False, {'ack': RoleType.COMMITTEE_ADMIN}) # 4
GRANT_CLOSED = 0
#states.State('Closed') # 0

state_field = views.StateField('Closed', 'Waiting', 'Ready', 'Exchanging Currency', 'Transferred')

ACTION_CHECKED = model.Action('checked', 'Funds Checked', RoleType.FUND_ADMIN, GRANT_READY, [GRANT_WAITING])
ACTION_EXCHANGE = model.Action('exchange', 'Exchange Requested', RoleType.PAYMENT_ADMIN, GRANT_CURRENCY_REQUESTED, [GRANT_READY])
ACTION_TRANSFERRED = model.Action('transferred', 'Transferred', RoleType.PAYMENT_ADMIN, GRANT_TRANSFERED, [GRANT_CURRENCY_REQUESTED])
ACTION_ACKNOWLEDGED = model.Action('ack', 'Received', RoleType.COMMITTEE_ADMIN, GRANT_CLOSED, [GRANT_TRANSFERED])
ACTION_CANCEL = model.Action('cancel', 'Cancel', RoleType.COMMITTEE_ADMIN, GRANT_CLOSED, [GRANT_WAITING])

class MoneyForm(wtforms.Form):
    currency = custom_fields.SelectField(choices=[('sterling', u'£'), ('ugx', u'Ush')],
                    widget=renderers.radio_field_widget)
    value = wtforms.IntegerField(validators=[wtforms.validators.NumberRange(min=100)])

class ExchangeCurrencyField:
    def __init__(self, label, to_currency):
        self.label = views.Label(label)
        self.to_currency = to_currency

    def get_display_value(self, entity):
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
    description = wtforms.TextAreaField()
    amount = wtforms.FormField(MoneyForm, label='Requested Amount', widget=renderers.form_field_widget)
    project = custom_fields.KeyPropertyField('Project',
                    validators=[wtforms.validators.InputRequired()],
                    query=db.Project.query(db.Project.state_index == 2))
    target_date = wtforms.DateField(widget=widgets.MonthInput(),
                                format='%Y-%m',
                                validators=[wtforms.validators.Optional()])

class ExchangeRateForm(wtforms.Form):
    action = wtforms.HiddenField(default='transferred')
    exchange_rate = wtforms.IntegerField('Exchange Rate', validators=[wtforms.validators.InputRequired()])

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
        return 'Grant to ' + entity.project.get().name + ' on ' + str(entity.target_date)

grant_model = GrantModel()

class GrantListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, grant_model, GrantForm)

    def get_fields(self, form):
        return (form._fields['project'], form._fields['amount'], state_field)

class GrantView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, grant_model, GrantForm, ACTION_CHECKED, ACTION_EXCHANGE, 
                ACTION_TRANSFERRED, ACTION_ACKNOWLEDGED, ACTION_CANCEL)

    def get_fields(self, form):
        creator = views.ReadOnlyKeyField('creator', 'Creator')
        rate = views.ReadOnlyField('exchange_rate', 'Exchange Rate')
        transferred_sterling = ExchangeCurrencyField(u'Transferred Amount £', 'sterling')
        transferred_ugx = ExchangeCurrencyField('Transferred Amount Ush', 'ugx')
        return form._fields.values() + [state_field, rate, transferred_sterling, transferred_ugx, creator]

    def process_action_button(self, action, entity, user, buttons, dialogs):
        if action.name != 'transferred':
            return views.EntityView.process_action_button(self, action, entity, user, buttons, dialogs)
        form = ExchangeRateForm(request.form)
        if (request.method == 'POST' and request.form.get('action') == 'transferred' 
                  and form.validate()):
            form.populate_obj(entity)
            entity.state_index = GRANT_TRANSFERED
            entity.put()
            return True
        rendered_form = renderers.render_form(form)
        dialog = renderers.render_modal_dialog(rendered_form, 'd-transferred', form.errors)
        dialogs.append(dialog)
        enabled = action.is_allowed(entity, user)
        button = renderers.render_modal_open(action.label, 'd-transferred', enabled)
        buttons.append(button)
        return False
    
def add_rules(app):
    app.add_url_rule('/grant_list/<db_id>', view_func=GrantListView.as_view('view_grant_list'))
    app.add_url_rule('/grant/<db_id>/', view_func=GrantView.as_view('view_grant'))
