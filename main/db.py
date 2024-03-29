#_*_ coding: UTF-8 _*_

from google.appengine.ext import ndb
import json
import role_types

class Money:
    def __init__(self, currency='sterling', value=None):
        self.currency = currency
        self.value = value
        
    def __repr__(self):
        return 'Money(currency=%s,value=%s)' % (self.currency, self.value)

    def __unicode__(self):
        if self.currency=='sterling':
            return u"£{:,}".format(self.value)
        else:
            return "{:,}".format(self.value) + ' Ush'

class MoneyProperty(ndb.StringProperty):
    def _validate(self, value):
        if not isinstance(value, Money):
            raise TypeError('expected a Money value, got %s' % repr(value))

    def _to_base_type(self, value):
        money_dict = { 'currency': value.currency, 'value': value.value }
        return json.dumps(money_dict)

    def _from_base_type(self, base):
        money_dict = json.loads(base)
        return Money(money_dict['currency'], money_dict['value'])

# Top level
class WorkBench(ndb.Model):
    last_ref_id = ndb.IntegerProperty(default=0)
    email_api_key = ndb.StringProperty()
    
# Top level
class User(ndb.Model):
    name = ndb.StringProperty()
    email = ndb.StringProperty()

# ancestor = User
class Role(ndb.Model):
    type_index = ndb.IntegerProperty()
    committee = ndb.StringProperty()

    @property
    def name(self):
        return dict(role_types.get_choices()).get(self.type_index, "")

# Top level
class Supplier(ndb.Model):
    name = ndb.StringProperty()
    receives_grants = ndb.BooleanProperty(default=False)
    paid_in_sterling = ndb.BooleanProperty(default=True)
    contact_emails = ndb.StringProperty(repeated = True)

# ancestor = Supplier
class SupplierFund(ndb.Model):
    name = ndb.StringProperty()
    description = ndb.StringProperty()
    partner_required = ndb.BooleanProperty(default=False)

# ancestor = Supplier
class Partner(ndb.Model):
    name = ndb.StringProperty()

# ancestor = Supplier
class ForeignTransfer(ndb.Model):
    ref_id = ndb.StringProperty()
    state_index = ndb.IntegerProperty(default=1)
    creator = ndb.KeyProperty(kind=User)
    exchange_rate = ndb.IntegerProperty()
    creation_date = ndb.DateProperty(auto_now_add = True)

    @property
    def name(self):
        return self.ref_id

# Top level
class Fund(ndb.Model):
    name = ndb.StringProperty()
    description = ndb.StringProperty()
    committee = ndb.StringProperty()
    code = ndb.StringProperty()
    state_index = ndb.IntegerProperty(default=1)

# ancestor = Fund
class InternalTransfer(ndb.Model):
    description = ndb.StringProperty()
    amount = MoneyProperty(default=Money())
    dest_fund = ndb.KeyProperty(kind=Fund)
    state_index = ndb.IntegerProperty(default=1)
    creator = ndb.KeyProperty(kind=User)
    
    @property
    def name(self):
        return "Transfer-To-" + self.dest_fund.get().name

# ancestor = Supplier
class Project(ndb.Model):
    name = ndb.StringProperty()
    description = ndb.StringProperty()
    committee = ndb.StringProperty()
    state_index = ndb.IntegerProperty(default=1)
    multi_committee = ndb.BooleanProperty()
    creator = ndb.KeyProperty(kind=User)
    partner = ndb.KeyProperty(kind=Partner)
    fund = ndb.KeyProperty(kind=SupplierFund)
    size = ndb.IntegerProperty(default=0)
    grant_agreement_start = ndb.DateProperty()

# ancestor = Fund
class Grant(ndb.Model):
    description = ndb.StringProperty()
    amount = MoneyProperty(default=Money())
    state_index = ndb.IntegerProperty(default=1)
    project = ndb.KeyProperty(kind=Project)
    creator = ndb.KeyProperty(kind=User)
    target_date = ndb.DateProperty()
    transfer = ndb.KeyProperty(kind=ForeignTransfer, default=None)
    supplier = ndb.KeyProperty(kind=Supplier)

    @property
    def name(self):
        return "Grant-" + self.project.get().name

def find_pending_grants(supplier, cutoff_date):
    return Grant.query(ndb.AND(Grant.target_date <= cutoff_date, 
                               Grant.supplier == supplier.key,
                               Grant.transfer == None,
                               Grant.state_index.IN([1, 2]))).order(Grant.target_date).fetch()

def find_ready_grants(supplier):
    return Grant.query(ndb.AND(Grant.supplier == supplier.key,
                               Grant.transfer == None,
                               Grant.state_index == 2)).fetch()

def find_pending_payments(supplier):
    return PurchasePayment.query(ndb.AND(PurchasePayment.supplier == supplier.key,
                               PurchasePayment.transfer == None,
                               PurchasePayment.paid == False)).fetch()

# ancestor = Fund
class Pledge(ndb.Model):
    description = ndb.StringProperty()
    amount = MoneyProperty(default=Money())
    ref_id = ndb.StringProperty()
    state_index = ndb.IntegerProperty(default=1)
    creator = ndb.KeyProperty(kind=User)

    @property
    def name(self):
        return self.ref_id

# ancestor = Payment
class PurchasePayment(ndb.Model):
    payment_type = ndb.StringProperty() # advance or invoice
    supplier = ndb.KeyProperty(kind=Supplier)
    amount = MoneyProperty(default=Money())
    transfer = ndb.KeyProperty(kind=ForeignTransfer, default=None)
    paid = ndb.BooleanProperty(default=False)

# ancestor = Fund
class Purchase(ndb.Model):
    description = ndb.StringProperty()
    quote_amount = MoneyProperty(default=Money())
    state_index = ndb.IntegerProperty(default=1)
    po_number = ndb.StringProperty()
    supplier = ndb.KeyProperty(kind=Supplier)
    creator = ndb.KeyProperty(kind=User)
    advance = ndb.KeyProperty(kind=PurchasePayment)
    invoice = ndb.KeyProperty(kind=PurchasePayment)

    @property
    def name(self):
        if self.po_number:
            return self.po_number
        return "Purchase"

class AuditRecord(ndb.Model):
    entity = ndb.KeyProperty()
    user = ndb.KeyProperty(kind=User)
    action = ndb.StringProperty()
    message = ndb.StringProperty()
    timestamp = ndb.DateTimeProperty(auto_now_add=True)
    parent = ndb.KeyProperty(default=None)
