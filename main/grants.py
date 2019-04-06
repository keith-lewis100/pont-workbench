#_*_ coding: UTF-8 _*_

import wtforms
import wtforms.widgets.html5 as widgets
from datetime import date, timedelta

import db
import data_models
import views
import custom_fields
import properties
from role_types import RoleType

STATE_WAITING = 1
STATE_READY = 2
STATE_TRANSFERED = 3
STATE_CLOSED = 0

state_labels = ['Closed', 'Waiting', 'Ready', 'Transferred']
def state_of(entity):
    return state_labels[entity.state_index]

def perform_create(model, action_name):
        form = self.get_form('create')
        if not form.validate():
            return False
        entity = model.entity
        form.populate_obj(entity)
        entity.creator = user.key
        supplier_fund = entity.project.parent()
        entity.supplier = supplier_fund.parent()
        entity.put()
        model.audit(action_name, "Create performed")
        return True

def perform_checked(model, action_name):
    model.entity.state_index = STATE_READY
    model.entity.put()
    model.audit(action_name, 'Checked performed')

ACTION_CHECKED = views.StateAction('checked', 'Funds Checked', RoleType.FUND_ADMIN,
                                   perform_checked, [STATE_WAITING])
ACTION_ACKNOWLEDGED = views.StateAction('ack', 'Received', RoleType.COMMITTEE_ADMIN,
                                        data_models.Model.perform_close, [STATE_TRANSFERED])
ACTION_CANCEL = views.cancel_action(RoleType.COMMITTEE_ADMIN, [STATE_WAITING, STATE_READY])
ACTION_UPDATE = views.update_action(RoleType.COMMITTEE_ADMIN, [STATE_WAITING])
ACTION_CREATE = views.Action('create', 'New', RoleType.COMMITTEE_ADMIN, perform_create)

state_field = properties.SelectProperty('state_index', 'State', enumerate(state_labels))

creator_field = properties.KeyProperty('creator', 'Requestor')
project_field = properties.KeyProperty('project')
amount_field = properties.StringProperty('amount')
transferred_amount_field = properties.StringProperty(data_models.calculate_transferred_amount, 'Transferred Amount')
source_field = properties.StringProperty(lambda e: e.key.parent().get().code, 'Source Fund')
target_date_field = properties.DateProperty('target_date', format='%Y-%m')

class GrantForm(wtforms.Form):
    amount = wtforms.FormField(custom_fields.MoneyForm, label='Requested Amount', widget=custom_fields.form_field_widget)
    project = custom_fields.SelectField(coerce=data_models.create_key, validators=[wtforms.validators.InputRequired()])
    target_date = wtforms.DateField(widget=widgets.MonthInput(), format='%Y-%m',
                                validators=[wtforms.validators.InputRequired()])
    description = wtforms.TextAreaField()

def create_grant_form(request_input, entity):
    form = GrantForm(request_input, obj=entity)
    fund = entity.key.parent().get()
    project_list = db.Project.query(db.Project.committee == fund.committee).fetch()
    custom_fields.set_field_choices(form._fields['project'], project_list)
    return form

class GrantListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, 'Grant', ACTION_CREATE)

    def load_entities(self, parent):
        return db.Grant.query(ancestor=parent.key).fetch()

    def create_entity(self, parent):
        entity = db.Grant(parent=parent.key)
        entity.target_date = date.today() + timedelta(30)
        return entity

    def create_form(self, request_input, entity):
        return create_grant_form(request_input, entity)

    def get_fields(self, form):
        return (target_date_field, project_field, amount_field, state_field)

class GrantView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, ACTION_UPDATE, 1, ACTION_CHECKED,
                ACTION_ACKNOWLEDGED, ACTION_CANCEL)
   
    def title(self, entity):
        return 'Grant on ' + str(entity.target_date)

    def create_form(self, request_input, entity):
        return create_grant_form(request_input, entity)

    def get_fields(self, form):
        return [state_field, creator_field, transferred_amount_field] + map(properties.create_readonly_field, 
                    form._fields.keys(), form._fields.values())

def add_rules(app):
    app.add_url_rule('/grant_list/<db_id>', view_func=GrantListView.as_view('view_grant_list'))
    app.add_url_rule('/grant/<db_id>/', view_func=GrantView.as_view('view_grant'))
