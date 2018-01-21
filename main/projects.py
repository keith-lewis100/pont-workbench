#_*_ coding: UTF-8 _*_

from flask import redirect, request, url_for
from flask.views import View
import wtforms

import model
import renderers
import custom_fields
import views
import logging
import states

PROJECT_APPROVAL_PENDING = states.State(0, 'Approval Pending', ('state-change', 1), ('update',))
PROJECT_APPROVED = states.State(1, 'Approved', ('create', 'Purchase'), ('create', 'Grant'), 
                                    ('create', 'Pledge'), ('update',))

projectStates = [PROJECT_APPROVAL_PENDING, PROJECT_APPROVED]

class ProjectForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    description = wtforms.TextAreaField()
    dest_fund = custom_fields.KeyPropertyField('Destination Fund',
                    validators=[wtforms.validators.InputRequired()],
                    query=model.cap_fund_query())

class Project(views.EntityType):
    def __init__(self):
        self.name = 'Project'
        self.formClass = ProjectForm

    def get_state(self, index):
        return projectStates[index]
        
    def create_entity(self, parent):
        return model.create_project(parent)

    def load_entities(self, parent):
        return model.list_projects(parent)
        
    def title(self, entity):
        return 'Project ' + entity.name
                
class ProjectListView(views.ListView):
    def __init__(self):
        self.entityType = Project()
        
    def get_fields(self, form):
        state = views.StateField(projectStates)
        return (form._fields['name'], state)

class ProjectView(views.EntityView):
    def __init__(self):
        self.entityType = Project()
        self.actions = [(1, 'Approve')]
        
    def get_fields(self, form):
        state = views.StateField(projectStates)
        return form._fields.values() + [state]
            
    def get_links(self, entity):
        purchases_url = url_for('view_purchase_list', db_id=entity.key.urlsafe())
        showPurchases = renderers.render_link('Show Purchase Requests', purchases_url, class_="button")
        grants_url = url_for('view_grant_list', db_id=entity.key.urlsafe())
        showGrants = renderers.render_link('Show Grants', grants_url, class_="button")
        pledges_url = url_for('view_pledge_list', db_id=entity.key.urlsafe())        
        showPledges = renderers.render_link('Show Pledges', pledges_url, class_="button")
        return [showPurchases, showGrants, showPledges]

class ProjectMenu(views.MenuView):
    def __init__(self):
        self.entityType = Project()

def add_rules(app):
    app.add_url_rule('/project_list/<db_id>', view_func=ProjectListView.as_view('view_project_list'))
    app.add_url_rule('/project/<db_id>/', view_func=ProjectView.as_view('view_project'))        
    app.add_url_rule('/project/<db_id>/menu', view_func=ProjectMenu.as_view('handle_project_menu'))
