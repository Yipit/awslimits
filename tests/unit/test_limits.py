import moto
from unittest import TestCase
from mock import patch
import os

mock_env = {
    'ROLE_ARN': 'arn:aws:iam::212311232123:role/test',
    'SENDGRID_API_KEY': '1231231231231231231',
}
with patch.dict(os.environ, mock_env):
    from awslimits.support import create_or_get_table


class TestDynamo(TestCase):
    def test_create_or_get_existing_table(self):
        create_or_get_table()

    def test_create_or_get_new_table(self):
        pass

    def test_create_or_get_table_exception(self):
        pass

    def test_create_or_get_table_failed(self):
        pass

