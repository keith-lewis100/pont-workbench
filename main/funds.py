#_*_ coding: UTF-8 _*_

from flask import url_for
import wtforms

import model
import renderers
import custom_fields
import views

class FundForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    committee = custom_fields.SelectField(choices=model.committee_labels)
    description = wtforms.TextAreaField()
    
class Fund(views.EntityType):
    def __init__(self):
        self.name = 'Fund'
        self.formClass = FundForm

    def get_state(self, index):
        return fundStates[index]
        
    def create_entity(self, parent):
        return model.create_fund()

    def load_entities(self, parent):
        return model.list_funds()
        
    def title(self, entity):
        return 'Fund ' + entity.name

class FundListView(views.ListView):
    def __init__(self):
        self.entityType = Fund()
        
    def get_fields(self, form):
        return (form._fields['name'],form._fields['committee'])
        
class FundView(views.EntityView):
    def __init__(self):
        self.entityType = Fund()
        self.actions = []
        
    def get_fields(self, form):
        return form._fields.values()
        
    def get_links(self, entity):
        projects_url = url_for('view_project_list', db_id=entity.key.urlsafe())
        showProjects = renderers.render_link('Show Projects', projects_url, class_="button")
        transfers_url = url_for('view_transfer_list', db_id=entity.key.urlsafe())
        showTransfers = renderers.render_link('Show Transfers', transfers_url, class_="button")        
        return [showProjects, showTransfers]

def add_rules(app):
    app.add_url_rule('/fund_list', view_func=FundListView.as_view('view_fund_list'))
    app.add_url_rule('/fund/<db_id>/', view_func=FundView.as_view('view_fund'))        
