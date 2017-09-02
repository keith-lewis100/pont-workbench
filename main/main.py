#_*_ coding: UTF-8 _*_
from flask import Flask, render_template, redirect, url_for, request
import wtforms
import model
import renderers
import custom_fields

app = Flask(__name__)

class ProjectForm(renderers.EntityRenderer):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    dest_fund = custom_fields.KeyPropertyField('Destination Fund', 
                  query=model.fund_query(('Organisation', 2)))

class MoneyForm(renderers.EntityRenderer):
    currency = wtforms.SelectField(choices=[('sterling', u'£'), ('ugx', u'Ush')],
                    widget=renderers.radio_field_widget)
    value = wtforms.DecimalField()

class GrantForm(renderers.EntityRenderer):
    amount = wtforms.FormField(MoneyForm, widget=renderers.form_field_widget)

@app.route('/')
def home():
    return redirect(url_for('view_project_list'))
    
@app.route('/projects', methods=['GET', 'POST'])
def view_project_list():
    project = model.create_project()
    form = ProjectForm(request.form, obj=project)
    if request.method == 'POST' and form.validate():
        form.populate_obj(project)
        app.logger.debug('new project=' + str(project))
        project.put()
        return redirect(url_for('view_project_list'))
    rendered_form = form.render_fields()
    projects = model.list_projects()
    entities = form.render_entity_list(None, projects)
    return render_template('entity_list.html', kind='Projects', entities=entities, create_form=rendered_form)
   
@app.route('/project/<project_id>/', methods=['GET'])
def view_project(project_id):
    project = model.lookup_entity(('Project', project_id))
    form = ProjectForm()
    menu = [ renderers.render_button('Show Grants', url='./grants')]
    entity = form.render_entity(None, project)
    return render_template('entity.html', kind='Project', menu=menu, entity=entity)

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
def view_grant(project_id, grant_id):
    grant = model.lookup_entity(('Project', project_id), ('Grant', grant_id))
    form = GrantForm(request.form, obj=grant)
    entity = form.render_entity(None, grant)
    menu = []
    return render_template('entity.html', kind='Grant', menu=menu, entity=entity)

@app.route('/supplier/<supplier_id>')
def view_supplier_payments(supplier_id):
    payments = model.list_supplier_payments(('Organisation', supplier_id))
    entities = form.render_entity_list(None, payments)
    return render_template('entity_list.html', kind='Payments', entities=entities, create_form=rendered_form)
    