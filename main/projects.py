#_*_ coding: UTF-8 _*_

from flask import redirect, request, url_for
from flask.views import View
import wtforms

import db
import model
import renderers
import custom_fields
import views
import logging
import states
from role_types import RoleType

PROJECT_APPROVAL_PENDING = states.State('Approval Pending', True, False, {1: RoleType.PROJECT_APPROVER}) # 0
PROJECT_APPROVED = states.State('Approved', True) # 1

projectStates = [PROJECT_APPROVAL_PENDING, PROJECT_APPROVED]

cap_key = db.Supplier.get_or_insert('mbale-cap', name='Mbale CAP').key

class ProjectForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    description = wtforms.TextAreaField()
    dest_fund = custom_fields.KeyPropertyField('Destination Fund',
                    validators=[wtforms.validators.InputRequired()],
                    query=db.SupplierFund.query(ancestor=cap_key))
    
class ProjectModel(model.EntityModel):
    def __init__(self):
        model.EntityModel.__init__(self, 'Project', RoleType.COMMITTEE_ADMIN, None, projectStates)

    def create_entity(self, parent):
        return db.Project(parent=parent.key)

    def load_entities(self, parent):
        return db.Project.query(ancestor=parent.key).fetch()
        
    def title(self, entity):
        return 'Project ' + entity.name

project_model = ProjectModel()
        
class ProjectListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, project_model, ProjectForm)
        
    def get_fields(self, form):
        state = views.StateField(projectStates)
        return (form._fields['name'], state)

class ProjectView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, project_model, ProjectForm, (1, 'Approve'))
        
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

def add_rules(app):
    app.add_url_rule('/project_list/<db_id>', view_func=ProjectListView.as_view('view_project_list'))
    app.add_url_rule('/project/<db_id>', view_func=ProjectView.as_view('view_project'))        
    app.add_url_rule('/project/<db_id>/menu', view_func=views.MenuView.as_view('handle_project_menu', project_model))
