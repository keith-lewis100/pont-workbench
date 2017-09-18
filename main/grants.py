#_*_ coding: UTF-8 _*_

from flask.views import View
import wtforms

import model
import renderers
import views

class MoneyForm(wtforms.Form):
    currency = wtforms.SelectField(choices=[('sterling', u'£'), ('ugx', u'Ush')],
                    widget=renderers.radio_field_widget)
    value = wtforms.IntegerField()

class GrantForm(wtforms.Form):
    amount = wtforms.FormField(MoneyForm, widget=renderers.form_field_widget)

class GrantListView(views.ListView):
    def __init__(self):
        self.kind = 'Grants'
        self.formClass = GrantForm
        
    def create_entity(self, db_id):
        return model.create_grant(db_id)

    def load_entities(self, db_id):
        return model.list_grants(db_id)
        
    def get_fields(self, entity):
        form = GrantForm()
        state = views.ReadOnlyField('state', 'State')
        return (form._fields['amount'], state)

class GrantView(views.EntityView):
    def __init__(self):
        self.kind = 'Grant'
        self.actions = []
        
    def get_fields(self, entity):
        form = GrantForm()
        state = views.ReadOnlyField('state', 'State')
        return (form._fields['amount'], state)
        
    def title(self, entity):
        return ""

    def get_links(self, entity):
        return ""

def add_rules(app):
    app.add_url_rule('/grant_list/<db_id>', view_func=GrantListView.as_view('view_grant_list'))
    app.add_url_rule('/grant/<db_id>/', view_func=GrantView.as_view('view_grant'))
