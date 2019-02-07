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
import supplier_funds
import internal_transfers
import purchases
import users
import roles
import paymentsdue
import partners

app = Flask(__name__)

@app.route('/')
def home():
    funds_url = url_for('view_fund_list')
    showFunds = renderers.render_link('Show Funds', funds_url, class_="button")
    suppliers_url = url_for('view_supplier_list')        
    showSuppliers = renderers.render_link('Show Suppliers', suppliers_url, class_="button")
    users_url = url_for('view_user_list')        
    showUsers = renderers.render_link('Show Users', users_url, class_="button")
    links = renderers.render_nav(showFunds, showSuppliers, showUsers)
    return render_template('layout.html', title='DashBoard', user=views.render_user(), main=links)

funds.add_rules(app)
projects.add_rules(app)
grants.add_rules(app)
pledges.add_rules(app)
suppliers.add_rules(app)
supplier_funds.add_rules(app)
internal_transfers.add_rules(app)
purchases.add_rules(app)
users.add_rules(app)
roles.add_rules(app)
paymentsdue.add_rules(app)
partners.add_rules(app)