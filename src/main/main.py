#_*_ coding: UTF-8 _*_
from flask import Flask, render_template, redirect, url_for, request
import logging
import wtforms

app = Flask(__name__)

class MoneyForm(wtforms.Form):
    currency = wtforms.RadioField(choices=[('sterling', u'£'), ('ugx', u'USh')])
    value = wtforms.DecimalField()

@app.route('/')
def home():
    project_url = '123456'
    return redirect(url_for('view_project', id=project_url))
    
@app.route('/project/<id>', methods=['GET', 'POST'])
def view_project(id):
    logging.info("view_project id=" + id)
    project = { 'name' : 'OVC-001', 'state': 'ACTIVE' }
    amount = { 'currency': 'ugx' }
    form = MoneyForm(request.form, obj=amount)
    if request.method == 'POST' and form.validate():
        logging.debug('amount=' + str(amount))
        return redirect('/success')
    return render_template('project.html', entity=project, form=form)

@app.route('/success')
def new_grant():
    return "Done"
