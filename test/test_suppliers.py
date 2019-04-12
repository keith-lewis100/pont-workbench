import unittest
from flask import Flask
from google.appengine.ext import ndb

import db
import suppliers
from application import app
from role_types import RoleType
from html_builder import html

class TestSuppliers(unittest.TestCase):
    def setUp(self):
        self.dbstate = ndb.clone()

    def tearDown(self):
        ndb.reset(self.dbstate)

    def test_view_supplier(self):
        supplier = db.Supplier(id=6)
        supplier.name = 'Sup-6'
        supplier.receives_grants = True
        supplier.paid_in_sterling = False
        supplier.put()
        with app.test_request_context('/', method='GET'):
            args = suppliers.view_supplier('Supplier-6')

    def test_create_payment(self):
        user = db.User.query().get()
        role = db.Role(parent=user.key)
        role.type_index = RoleType.PAYMENT_ADMIN
        role.put()
        supplier = db.Supplier(id=6)
        supplier.paid_in_sterling = False
        supplier.name = "Sup-6"
        supplier.put()
        grant = db.Grant()
        grant.put()
        with app.test_request_context('/supplier/123', method='POST', data={
               '_action': 'startTransfer'
            }):
            url = suppliers.view_supplier('Supplier-6')
        self.assertEquals('/foreigntransfer/ForeignTransfer-5', url)

    def test_create_payment_no_grants(self):
        user = db.User.query().get()
        role = db.Role(parent=user.key)
        role.type_index = RoleType.PAYMENT_ADMIN
        role.put()
        supplier = db.Supplier(id=6)
        supplier.paid_in_sterling = False
        supplier.name = "Sup-6"
        supplier.put()
        with app.test_request_context('/supplier/123', method='POST', data={
               '_action': 'startTransfer'
            }):
            args = suppliers.view_supplier('Supplier-6')
        expected = html.div(html.div('No grants are pending - nothing to transfer',
                                     class_='error'))
        self.assertEquals(expected, args.get('errors'))

if __name__ == '__main__':
   unittest.main()
