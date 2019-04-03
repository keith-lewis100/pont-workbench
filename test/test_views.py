import unittest
from flask import Flask
from google.appengine.ext import ndb

import views
import data_models
import db
from html_builder import html

class TestViews(unittest.TestCase):
    def test_view_breadcrumbs_none(self):
        crumbs = views.view_breadcrumbs(None)
        expected = html.div(html.a('Dashboard', href='/'))
        self.assertEqual(expected, crumbs)

    def test_view_breadcrumbs_list(self):
        committee = data_models.Committee('EDU', 'Education')
        crumbs = views.view_breadcrumbs(None, 'Committee')
        expected = html.div(html.a('Dashboard', href='/'), ' / ',
                    html.a('Committee List', href='/committee_list'))
        self.assertEqual(expected, crumbs)

    def test_view_breadcrumbs_committee(self):
        committee = data_models.Committee('EDU', 'Education')
        crumbs = views.view_breadcrumbs(committee)
        expected = html.div(html.a('Dashboard', href='/'), ' / ',
                    html.a('Committee List', href='/committee_list'), ' / ',
                    html.a('Education', href='/committee/EDU'))
        self.assertEqual(expected, crumbs)

    def test_view_breadcrumbs_list2(self):
        role = db.Role.query().get()
        user = role.key.parent().get()
        user_id = user.key.urlsafe()
        crumbs = views.view_breadcrumbs(user, 'Role')
        expected = html.div(html.a('Dashboard', href='/'), ' / ',
                    html.a('User List', href='/user_list'), ' / ',
                    html.a('Keith', href='/user/' + user_id), ' / ',
                    html.a('Role List', href='/role_list/' + user_id))
        self.assertEqual(expected, crumbs)

if __name__ == '__main__':
   unittest.main()
