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

class GrantCreate(model.CreateAction):
    def apply_to(self, entity, user):
        entity.creator = user.key
        fund = entity.project.parent()
        entity.supplier = fund.parent()
        entity.put()

ACTION_CHECKED = model.StateAction('checked', 'Funds Checked', RoleType.FUND_ADMIN, GRANT_READY, [GRANT_WAITING])
ACTION_ACKNOWLEDGED = model.StateAction('ack', 'Received', RoleType.COMMITTEE_ADMIN, GRANT_CLOSED, [GRANT_TRANSFERED])
ACTION_CANCEL = model.StateAction('cancel', 'Cancel', RoleType.COMMITTEE_ADMIN, GRANT_CLOSED, [GRANT_WAITING])
ACTION_UPDATE = model.StateAction('edit', 'Edit', RoleType.COMMITTEE_ADMIN, None, [GRANT_WAITING])
ACTION_CREATE = GrantCreate(RoleType.COMMITTEE_ADMIN)

state_field = readonly_fields.StateField('Closed', 'Waiting', 'Ready', 'Transferred')
creator_field = readonly_fields.ReadOnlyKeyField('creator', 'Requestor')
project_field = readonly_fields.ReadOnlyKeyField('project')
amount_field = readonly_fields.ReadOnlyField('amount')
transferred_amount_field = readonly_fields.ExchangeCurrencyField('#', 'Transferred Amount')
source_field = readonly_fields.ReadOnlyField('^.code', 'Source Fund')
target_date_field = readonly_fields.DateField('target_date', format='%Y-%m')

class GrantForm(wtforms.Form):
    amount = wtforms.FormField(custom_fields.MoneyForm, label='Requested Amount', widget=custom_fields.form_field_widget)
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
        return [state_field, creator_field, transferred_amount_field] + map(readonly_fields.create_readonly_field, 
                    form._fields.keys(), form._fields.values())

def add_rules(app):
    app.add_url_rule('/grant_list/<db_id>', view_func=GrantListView.as_view('view_grant_list'))
    app.add_url_rule('/grant/<db_id>/', view_func=GrantView.as_view('view_grant'))
