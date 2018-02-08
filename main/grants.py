#_*_ coding: UTF-8 _*_

from flask.views import View
import wtforms

import db
import model
import renderers
import views
import custom_fields
import states
from role_types import RoleType
from projects import project_model

GRANT_TRANSFER_PENDING = states.State('TransferPending', True, False)
GRANT_TRANSFERED = states.State('Transferred')

grantStates = [GRANT_TRANSFER_PENDING, GRANT_TRANSFERED]

class MoneyForm(wtforms.Form):
    currency = custom_fields.SelectField(choices=[('sterling', u'£'), ('ugx', u'Ush')],
                    widget=renderers.radio_field_widget)
    value = wtforms.IntegerField(validators=[wtforms.validators.NumberRange(min=100)])

class GrantForm(wtforms.Form):
    description = wtforms.TextAreaField()
    amount = wtforms.FormField(MoneyForm, widget=renderers.form_field_widget)

class GrantModel(model.EntityModel):
    def __init__(self):
        model.EntityModel.__init__(self, 'Grant', RoleType.COMMITTEE_ADMIN, project_model, grantStates)
        
    def create_entity(self, parent):
        return db.Grant(parent=parent.key)

    def load_entities(self, parent):
        return db.Grant.query(ancestor=parent.key).fetch()
        
    def title(self, entity):
        return 'Grant'

grant_model = GrantModel()

class GrantListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, grant_model, GrantForm)

    def get_fields(self, form):
        state = views.StateField(grantStates)
        return (form._fields['amount'], state)

class GrantView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, grant_model, GrantForm)
        
    def get_fields(self, form):
        state = views.StateField(grantStates)
        creator = views.ReadOnlyKeyField('creator', 'Creator')
        return form._fields.values() + [state, creator]
        
    def get_links(self, entity):
        return []

def add_rules(app):
    app.add_url_rule('/grant_list/<db_id>', view_func=GrantListView.as_view('view_grant_list'))
    app.add_url_rule('/grant/<db_id>/', view_func=GrantView.as_view('view_grant', grant_model))
