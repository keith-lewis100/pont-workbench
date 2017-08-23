#_*_ coding: UTF-8 _*_
from flask import Flask, render_template, redirect, url_for, request
import logging
import wtforms

app = Flask(__name__)

grants = []

class ProjectForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])

class MoneyForm(wtforms.Form):
    currency = wtforms.RadioField(choices=[('sterling', u'£'), ('ugx', u'Ush')])
    value = wtforms.DecimalField()

class GrantForm(wtforms.Form):
    amount = wtforms.FormField(MoneyForm)

@app.route('/')
def home():
    project_url = '123456'
    return redirect(url_for('view_project', id=project_url))
    
@app.route('/project/<id>/', methods=['GET'])
def view_project(id):
    app.logger.debug('view_project id=' + id)
    project = { 'name' : 'OVC-001', 'state': 'ACTIVE' }
    return render_template('project.html', entity=project)

@app.route('/project/<id>/grants', methods=['GET', 'POST'])
def view_grant_list(id):
    app.logger.debug('view_project id=' + id)
    grant = { 'amount': { 'currency': 'ugx' , 'value': 0 }}
    add_form = GrantForm(request.form, obj=grant)
    if request.method == 'POST' and add_form.validate():
#        add_form.populate_obj(grant)
        app.logger.debug('grant=' + str(grant))
        grants.append(grant)
        return redirect(url_for('view_grant_list', id=id))
    return render_template('grants.html', entities=grants, add=add_form)
