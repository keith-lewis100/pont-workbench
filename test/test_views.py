import unittest
from flask import Flask
from google.appengine.ext import ndb

import views
import data_models
import db
from html_builder import html

class TestViews(unittest.TestCase):
    def test_create_breadcrumbs_none(self):
        dash = views.create_breadcrumbs(None)
        expected = [html.a('Dashboard', href='/')]
        self.assertEqual(expected, dash)

    def test_create_breadcrumbs_list(self):
        committee = data_models.Committee('EDU', 'Education')
        dash = views.create_breadcrumbs_list(committee)
        expected = [html.a('Dashboard', href='/'), ' / ',
                    html.a('Committee List', href='/committee_list')]
        self.assertEqual(expected, dash)

    def test_create_breadcrumbs_committee(self):
        committee = data_models.Committee('EDU', 'Education')
        dash = views.create_breadcrumbs(committee)
        expected = [html.a('Dashboard', href='/'), ' / ',
                    html.a('Committee List', href='/committee_list'), ' / ',
                    html.a('Education', href='/committee/EDU')]
        self.assertEqual(expected, dash)

    def test_create_breadcrumbs_list2(self):
        role = db.Role.query().get()
        user_id = role.key.parent().urlsafe()
        dash = views.create_breadcrumbs_list(role)
        expected = [html.a('Dashboard', href='/'), ' / ',
                    html.a('User List', href='/user_list'), ' / ',
                    html.a('Keith', href='/user/' + user_id), ' / ',
                    html.a('Role List', href='/role_list/' + user_id)]
        self.assertEqual(expected, dash)

if __name__ == '__main__':
   unittest.main()
