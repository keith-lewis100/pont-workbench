#_*_ coding: UTF-8 _*_

from flask import url_for
from application import app

import data_models
import renderers
import properties
import views

committee_field_list = (properties.StringProperty('name'), )

@app.route('/committee_list', methods=['GET'])
def view_committee_list():
    breadcrumbs = views.create_breadcrumbs(None)
    supplier_field_list = (properties.StringProperty('name'), )
    committee_list = data_models.get_committee_list()
    entity_table = views.render_entity_list(committee_list, committee_field_list)
    return views.render_view('Committee List', breadcrumbs, entity_table)

@app.route('/committee/<db_id>', methods=['GET'])
def view_committee(db_id):
    committee = data_models.lookup_committee(db_id)
    breadcrumbs = views.create_breadcrumbs_list(committee)
    content = views.render_entity(committee,committee_field_list)
    funds_url = url_for('view_fund_list', db_id=db_id)
    showFunds = renderers.render_link('Show Funds', funds_url, class_="button")        
    title = 'Committee ' + committee.name
    return views.render_view(title, breadcrumbs, content, links=[showFunds])
