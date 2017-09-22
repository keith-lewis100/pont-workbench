#_*_ coding: UTF-8 _*_

from flask import Flask, url_for, render_template
from flask.views import View
#_*_ coding: UTF-8 _*_

import wtforms

import renderers
import views

import funds
import projects
import grants
import pledges
import suppliers
import internal_transfers

app = Flask(__name__)

@app.route('/')
def home():
    funds_url = url_for('view_pont_fund_list')
    showFunds = renderers.render_link('Show Funds', url=funds_url, class_="button")
    suppliers_url = url_for('view_supplier_list')        
    showSuppliers = renderers.render_link('Show Suppliers', url=suppliers_url, class_="button")
    links = renderers.render_div(showFunds, showSuppliers)
    return render_template('entity.html', title='DashBoard', links=links, menu="", 
                    edit_dialog="", entity="")

funds.add_rules(app)
projects.add_rules(app)
grants.add_rules(app)
pledges.add_rules(app)
suppliers.add_rules(app)
internal_transfers.add_rules(app)
