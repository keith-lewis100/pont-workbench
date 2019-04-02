import unittest
from flask import Flask
from google.appengine.ext import ndb

import db
import purchases
from application import app
import funds
import committees
from role_types import RoleType

funds.add_rules(app)

class TestPurchases(unittest.TestCase):
    def test_purchase_list(self):
        with app.test_request_context('/', method='GET'):
            purchases.view_purchase_list('Fund-11')

    def test_create_purchase(self):
        role = db.Role()
        role.type_index = RoleType.COMMITTEE_ADMIN
        role.committee = 'EDU'
        role.put()
        fund = db.Fund(id=11)
        fund.committee = 'EDU'
        fund.name = 'myFund'
        fund.put()
        supplier = db.Supplier(id=6)
        supplier.name = 'S1'
        supplier.put()
        with app.test_request_context('/', method='POST', data={
               '_action': 'create',
               'supplier': 'Supplier-6',
               'quote_amount-value': '11',
               'description': 'b'
            }):
            purchases.view_purchase_list('Fund-11')
        
    def test_update(self):
        role = db.Role()
        role.type_index = RoleType.COMMITTEE_ADMIN
        role.committee = 'EDU'
        role.put()
        supplier = db.Supplier(id=6)
        supplier.name = 'S1'
        supplier.put()
        self.assertEquals(db.create_key('Supplier-6'), supplier.key)
        fund = db.Fund(id=11)
        fund.committee = 'EDU'
        fund.name = 'myFund'
        fund.put()
        purchase = db.Purchase(id=12, parent=fund.key)
        purchase.description = 'a'
        purchase.put()
        with app.test_request_context('/p', method='POST', data={
               '_action': 'update',
               'supplier': 'Supplier-6',
               'quote_amount-value': '11',
               'description': 'b'
            }):
            purchases.view_purchase('Purchase-12')
        self.assertEqual('b', purchase.description)

    def test_checked(self):
        role = db.Role()
        role.type_index = RoleType.FUND_ADMIN
        role.put()
        fund = db.Fund(id=11)
        purchase = db.Purchase(id=12)
        purchase.put()
        with app.test_request_context('/p', method='POST', data={
               '_action': 'checked'
            }):
            purchases.view_purchase('Purchase-12')
        self.assertEqual("MB0001", purchase.po_number)

    def test_render_update_button(self):
        fund = db.Fund(id=11)
        fund.committee = 'EDU'
        fund.name = 'myFund'
        fund.put()
        purchase = db.Purchase(id=12, parent=fund.key)
        purchase.po_number = 'MB006'
        purchase.state_index = 1
        purchase.quote_amount = db.Money(value=1234)
        purchase.description = "desc"
        purchase.put()
        model = purchases.load_purchase_model('Purchase-12', None)
        with app.test_request_context('/', method='GET'):
            update = purchases.ACTION_UPDATE.render(model)
        self.assertEquals(2, len(update))
#        print update[1].__html__()

if __name__ == '__main__':
   unittest.main()
