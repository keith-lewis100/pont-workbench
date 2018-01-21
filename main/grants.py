#_*_ coding: UTF-8 _*_

from flask.views import View
import wtforms

import model
import renderers
import views
import custom_fields
import states

GRANT_TRANSFER_PENDING = states.State(0, 'Transfer Pending', ('update',))
GRANT_TRANSFERED = states.State(1, 'Transferred')
grantStates = [GRANT_TRANSFER_PENDING, GRANT_TRANSFERED]

class MoneyForm(wtforms.Form):
    currency = custom_fields.SelectField(choices=[('sterling', u'£'), ('ugx', u'Ush')],
                    widget=renderers.radio_field_widget)
    value = wtforms.IntegerField(validators=[wtforms.validators.NumberRange(min=100)])

class GrantForm(wtforms.Form):
    description = wtforms.TextAreaField()
    amount = wtforms.FormField(MoneyForm, widget=renderers.form_field_widget)
    
class Grant(views.EntityType):
    def __init__(self):
        self.name = 'Grant'
        self.formClass = GrantForm

    def get_state(self, index):
        return grantStates[index]
        
    def create_entity(self, parent):
        return model.create_grant(parent)

    def load_entities(self, parent):
        return model.list_grants(parent)
        
    def title(self, entity):
        return 'Grant'

class GrantListView(views.ListView):
    def __init__(self):
        self.entityType = Grant()

    def get_fields(self, form):
        state = views.StateField(grantStates)
        return (form._fields['amount'], state)

class GrantView(views.EntityView):
    def __init__(self):
        self.entityType = Grant()
        self.actions = []
        
    def get_fields(self, form):
        state = views.StateField(grantStates)
        creator = views.ReadOnlyKeyField('creator', 'Creator')
        return form._fields.values() + [state, creator]
        
    def get_links(self, entity):
        return []

def add_rules(app):
    app.add_url_rule('/grant_list/<db_id>', view_func=GrantListView.as_view('view_grant_list'))
    app.add_url_rule('/grant/<db_id>/', view_func=GrantView.as_view('view_grant'))
