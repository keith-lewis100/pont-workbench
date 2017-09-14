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
    dest_fund = custom_fields.KeyPropertyField('Destination Fund',
                    validators=[wtforms.validators.InputRequired()],
                    query=model.cap_fund_query())

class ProjectListView(views.ListView):
    def __init__(self):
        self.kind = 'Projects'
        self.formClass = ProjectForm
        
    def create_entity(self):
        return model.create_project(None)

    def load_entities(self):
        return model.list_projects(None)
        
    def get_fields(self, entity):
        form = ProjectForm()
        state = views.ReadOnlyField('state', 'State')
        return (form._fields['name'], state)

class ProjectView(views.EntityView):
    def __init__(self):
        self.kind = 'Project'
        
    def lookup_entity(self, project_id):
        return  model.lookup_entity(project_id)
        
    def get_fields(self, entity):
        form = ProjectForm()
        state = views.ReadOnlyField('state', 'State')
        return form._fields.values() + [state]
    
    def title(self, entity):
        return entity.name
        
    def get_menu(self, entity):
        url = url_for('view_grant_list', project_id=entity.key.urlsafe())
        showGrants = renderers.render_link('Show Grants', url=url, class_="button")
        approveEnabled = model.is_action_allowed('approve', entity)
        approve = renderers.render_button('Approve', name='action', value='approve', 
                        disabled=not approveEnabled)
        return renderers.render_form(showGrants, approve, action='./menu')

class ProjectMenuView(View):
    methods = ['POST']
    
    def dispatch_request(self, project_id):
        entity = model.lookup_entity(project_id)
        action = request.form['action']
        model.perform_action(action, entity)
        return redirect('/project/' + project_id)

def add_rules(app):
    app.add_url_rule('/project_list', view_func=ProjectListView.as_view('view_project_list'))
    app.add_url_rule('/project/<project_id>/', view_func=ProjectView.as_view('view_project'))        
    app.add_url_rule('/project/<project_id>/menu', view_func=ProjectMenuView.as_view('handle_project_menu'))
