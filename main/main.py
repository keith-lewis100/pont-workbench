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
import purchases
import users

app = Flask(__name__)

@app.route('/')
def home():
    funds_url = url_for('view_pont_fund_list')
    showFunds = renderers.render_link('Show Funds', funds_url)
    suppliers_url = url_for('view_supplier_list')        
    showSuppliers = renderers.render_link('Show Suppliers', suppliers_url)
    users_url = url_for('view_user_list')        
    showUsers = renderers.render_link('Show Users', users_url)
    links = renderers.render_nav(showFunds, showSuppliers, showUsers)
    return render_template('entity.html', title='DashBoard', user=views.render_user(), links=links, 
                    menu="", edit_dialog="", entity="")

funds.add_rules(app)
projects.add_rules(app)
grants.add_rules(app)
pledges.add_rules(app)
suppliers.add_rules(app)
internal_transfers.add_rules(app)
purchases.add_rules(app)
users.add_rules(app)