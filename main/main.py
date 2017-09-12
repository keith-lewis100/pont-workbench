#_*_ coding: UTF-8 _*_

from flask import Flask, redirect

import projects
import grants
import suppliers
app = Flask(__name__)

@app.route('/')
def home():
    return redirect('/projects')

projects.add_rules(app)
grants.add_rules(app)
suppliers.add_rules(app)
