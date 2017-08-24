from google.appengine.ext import ndb
import db

pont = db.Organisation.get_or_insert('pont', name='PONT')

def list_funds():
    funds = db.Fund.query(ancestor=pont.key).fetch()
    items = []
    for f in funds:
        item = f.key.urlsafe(), f.to_dict
        items.append(item)
    return items
    
def list_projects(fund_url):
    key = ndb.Key(urlsafe=fund_url)
    projects = db.Project.query(ancestor=key).fetch()
    items = []
    for p in projects:
        item = p.key.urlsafe(), p.to_dict
        items.append(item)
    return items
    
def lookup_project(project_url):
    key = ndb.Key(urlsafe=project_url)
    project = key.get()
    return project_url, project.to_dict()
    
def create_pont_fund(name):
    fund = db.Fund(parent=pont.key, name=name)
    return fund.put().urlsafe(), fund.to_dict()
    
def create_project(fund_url, name):
    key = ndb.Key(urlsafe=fund_url)
    project = db.Project(parent=key, name=name)
    return project.put().urlsafe(), project

def create_grant(project_url, amount):
    key = ndb.Key(urlsafe=project_url)
    grant = db.Grant(parent=key, state=0, amount=amount)
    return grant.put().urlsafe(), grant
