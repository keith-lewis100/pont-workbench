#_*_ coding: UTF-8 _*_

from flask import redirect, request, url_for
from flask.views import View
import wtforms

import model
import renderers
import custom_fields
import views
import logging

class ProjectForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    description = wtforms.TextAreaField()
    dest_fund = custom_fields.KeyPropertyField('Destination Fund',
                    validators=[wtforms.validators.InputRequired()],
                    query=model.cap_fund_query())

class ProjectListView(views.ListView):
    def __init__(self):
        self.kind = 'Project'
        self.formClass = ProjectForm
        
    def create_entity(self, parent):
        return model.create_project(parent)

    def load_entities(self, parent):
        return model.list_projects(parent)
                
    def get_fields(self, form):
        state = views.ReadOnlyField('state', 'State')
        return (form._fields['name'], state)

class ProjectView(views.EntityView):
    def __init__(self):
        self.formClass = ProjectForm
        self.actions = [(1, 'Approve')]
        
    def get_fields(self, form):
        state = views.ReadOnlyField('state', 'State')
        return form._fields.values() + [state]
    
    def title(self, entity):
        return 'Project ' + entity.name
        
    def get_links(self, entity):
        grants_url = url_for('view_purchase_list', db_id=entity.key.urlsafe())
        showPurchases = renderers.render_link('Show Purchase Requests', grants_url)
        grants_url = url_for('view_grant_list', db_id=entity.key.urlsafe())
        showGrants = renderers.render_link('Show Grants', grants_url)
        pledges_url = url_for('view_pledge_list', db_id=entity.key.urlsafe())        
        showPledges = renderers.render_link('Show Pledges', pledges_url)
        return renderers.render_nav(showPurchases, showGrants, showPledges)

def add_rules(app):
    app.add_url_rule('/project_list/<db_id>', view_func=ProjectListView.as_view('view_project_list'))
    app.add_url_rule('/project/<db_id>/', view_func=ProjectView.as_view('view_project'))        
    app.add_url_rule('/project/<db_id>/menu', view_func=views.MenuView.as_view('handle_project_menu'))
