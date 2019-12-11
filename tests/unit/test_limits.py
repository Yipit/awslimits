from __future__ import absolute_import


import moto
from unittest import TestCase
import os


class DynamoHelpersTestCase(TestCase):
    def setUp(self):
        os.environ['ROLE_ARN'] = 'arn:aws:iam::212311232123:role/test'
        os.environ['SENDGRID_API_KEY'] = '1231231231231231231'
        from awslimits.support import create_or_get_table

    # unset these env vars

    def test_create_or_get_existing_table(self):
        pass


    def test_create_or_get_new_table(self):
        pass


    def test_create_or_get_table_exception(self):
        pass


    def test_create_or_get_table_failed(self):
        pass

