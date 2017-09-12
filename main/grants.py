#_*_ coding: UTF-8 _*_

from flask.views import View
import wtforms

import model
import renderers
import views

class MoneyForm(wtforms.Form):
    currency = wtforms.SelectField(choices=[('sterling', u'£'), ('ugx', u'Ush')],
                    widget=renderers.radio_field_widget)
    value = wtforms.DecimalField()

class GrantForm(wtforms.Form):
    amount = wtforms.FormField(MoneyForm, widget=renderers.form_field_widget)


class GrantListView(views.ListView):
    def __init__(self):
        self.kind = 'Grants'
        self.formClass = GrantForm
        
    def create_entity(self, project_id):
        return model.create_grant(('Project', project_id))

    def load_entities(self, project_id):
        return model.list_grants(('Project', project_id))

class GrantView(views.EntityView):
    def __init__(self):
        self.kind = 'Grant'
        
    def lookup_entity(self, project_id, grant_id):
        return  model.lookup_entity(('Project', project_id), ('Grant', grant_id))
 
    def get_fields(self, entity):
        return GrantForm()._fields.values()
        
    def title(self, entity):
        return ""

    def get_menu(self, entity):
        return ""

def add_rules(app):
    app.add_url_rule('/project/<project_id>/grants', view_func=GrantListView.as_view('view_grant_list'))
    app.add_url_rule('/project/<project_id>/grant/<grant_id>/', view_func=GrantView.as_view('view_grant'))
