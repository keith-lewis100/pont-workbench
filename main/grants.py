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
import states
from role_types import RoleType
from projects import project_model

GRANT_WAITING = states.State('Waiting', True,
              {'checked': RoleType.FUND_ADMIN, 'cancel': RoleType.COMMITTEE_ADMIN}) # 1
GRANT_READY = states.State('Ready', False, {'transferred': RoleType.PAYMENT_ADMIN}) # 2
GRANT_TRANSFERED = states.State('Transferred', False, {'ack': RoleType.COMMITTEE_ADMIN}) # 3
GRANT_CLOSED = states.State('Closed') # 0
state_map = {
    'checked': 2,
    'transferred': 3,
    'ack': 0,
    'cancel': 0
}

grantStates = [GRANT_CLOSED, GRANT_WAITING, GRANT_READY, GRANT_TRANSFERED]

class MoneyForm(wtforms.Form):
    currency = custom_fields.SelectField(choices=[('sterling', u'£'), ('ugx', u'Ush')],
                    widget=renderers.radio_field_widget)
    value = wtforms.IntegerField(validators=[wtforms.validators.NumberRange(min=100)])

class GrantForm(wtforms.Form):
    description = wtforms.TextAreaField()
    amount = wtforms.FormField(MoneyForm, widget=renderers.form_field_widget)
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
        model.EntityModel.__init__(self, 'Grant', RoleType.COMMITTEE_ADMIN, project_model, grantStates)
        
    def create_entity(self, parent):
        entity = db.Grant(parent=parent.key)
        entity.target_date = date.today() + timedelta(30)
        return entity

    def load_entities(self, parent):
        return db.Grant.query(ancestor=parent.key).fetch()
        
    def title(self, entity):
        return 'Grant to ' + entity.project.get().name + ' on ' + str(entity.target_date)

    def perform_state_change(self, entity, action):
        entity.state_index = state_map.get(action)

grant_model = GrantModel()

class GrantListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, grant_model, GrantForm)

    def get_fields(self, form):
        state = views.StateField(grantStates)
        return (form._fields['project'], form._fields['amount'], state)

class GrantView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, grant_model, GrantForm, ('checked', 'Funds Checked'), 
                   ('transferred', 'Transferred'), ('ack', 'Received'), ('cancel', 'Cancel'))

    def get_fields(self, form):
        state = views.StateField(grantStates)
        creator = views.ReadOnlyKeyField('creator', 'Creator')
        rate = views.ReadOnlyField('exchange_rate', 'Exchange Rate')
        return form._fields.values() + [state, rate, creator]

    def process_action_button(self, action, label, enabled, entity, buttons, dialogs):
        if action != 'transferred':
            return views.EntityView.process_action_button(self, action, label, 
                                        enabled, entity, buttons, dialogs)
        form = ExchangeRateForm(request.form)
        if (request.method == 'POST' and request.form.get('action') == 'transferred' 
                  and form.validate()):
            form.populate_obj(entity)
            entity.state_index = 3
            entity.put()
            return True
        rendered_form = renderers.render_form(form)
        dialog = renderers.render_modal_dialog(rendered_form, 'd-transferred', form.errors)
        dialogs.append(dialog)
        button = renderers.render_modal_open(label, 'd-transferred', enabled)
        buttons.append(button)
        return False
    
def add_rules(app):
    app.add_url_rule('/grant_list/<db_id>', view_func=GrantListView.as_view('view_grant_list'))
    app.add_url_rule('/grant/<db_id>/', view_func=GrantView.as_view('view_grant'))
    app.add_url_rule('/grant/<db_id>/menu', view_func=views.MenuView.as_view('handle_grant_menu', grant_model))
