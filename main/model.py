import db

pont = db.Organisation.get_or_insert('pont', name='PONT')

def list_funds():
    return db.Fund.query(ancestor=pont.key).fetch()
    
def list_projects(**key_args):
    key = db.createKey(key_args)
    return db.Project.query(ancestor=key).fetch()
    
def lookup_project(**key_args):
    key = db.createKey(key_args)
    return key.get()
    
def create_pont_fund():
    return db.Fund(parent=pont.key)
    
def create_project(**key_args):
    key = db.createKey(key_args)
    return db.Project(parent=key)

def create_grant(**key_args):
    key = db.createKey(key_args)
    return db.GrantInstallment(parent=key)

def list_grants(**key_args):
    key = db.createKey(key_args)
    return db.GrantInstallment.query(ancestor=key).fetch()
