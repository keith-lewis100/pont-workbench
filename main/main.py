#_*_ coding: UTF-8 _*_
from flask import Flask, render_template, redirect, url_for, request
import logging
import wtforms
from dummy import model
import renderers

app = Flask(__name__)

class ProjectForm(renderers.EntityRenderer):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])

class MoneyForm(renderers.EntityRenderer):
    currency = wtforms.SelectField(choices=[('sterling', u'£'), ('ugx', u'Ush')],
                                  widget=renderers.radio_field_widget)
    value = wtforms.DecimalField()

class GrantForm(renderers.EntityRenderer):
    amount = wtforms.FormField(MoneyForm, widget=renderers.form_field_widget)

@app.route('/')
def home():
    projects = model.list_projects()
    key = projects[0].key
    return redirect(url_for('view_project', project_id=key.id()))
    
@app.route('/project/<project_id>/', methods=['GET'])
def view_project(project_id):
    project = model.lookup_project(('Project', project_id))
    form = ProjectForm()
    entity = form.render_entity(None, project)
    return render_template('entity.html', kind='Project', entity=entity)

@app.route('/project/<project_id>/grants', methods=['GET', 'POST'])
def view_grant_list(project_id):
    grant = model.create_grant(('Project', project_id))
    form = GrantForm(request.form, obj=grant)
    if request.method == 'POST' and form.validate():
        form.populate_obj(grant)
        app.logger.debug('new grant=' + unicode(grant))
        grant.put()
        return redirect(url_for('view_grant_list', project_id=project_id))
    rendered_form = form.render_fields(['amount'])
    grants = model.list_grants(('Project', project_id))
    entities = form.render_entity_list(None, grants)
    return render_template('entity_list.html', kind='Grants', entities=entities, create_form=rendered_form)

@app.route('/project/<project_id>/grant/<grant_id>', methods=['GET'])
def view_grant(project_id):
    grant = model.lookup_grant(('Project', project_id), ('Grant', grant_id))
    form = GrantForm(request.form, obj=grant)
    entity = form.render_entity(None, grant)
    return render_template('entity.html', kind='Grant', entity=entity)
