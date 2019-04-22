import os
import unittest
from unittest.mock import patch
from nose.tools import assert_true
from src.services.db_service import DbService
from src.tests.behaviored_mock import BehavioredMock

class MockPsycopg2Cursor(BehavioredMock):
    def __init__(self, behaviors = {}):
        super().__init__(behaviors)

    def execute(self, query, args):
        if self.has_throw_for_type('execute'):
            raise Exception('exception:execute')
        return

    def close(self):
        if self.has_throw_for_type('close'):
            raise Exception('exception:close')
        return

    def fetchall(self):
        if self.has_throw_for_type('fetchall'):
            raise Exception('exception:fetchall')
        if self.has_response_list('fetchall'):
            return self.get_response_list('fetchall')
        return []

class MockPsycopg2(BehavioredMock):
    def __init__(self, behaviors = {}):
        super().__init__(behaviors)
        self.autocommit = True

    def connect(self, **kwargs):
        if self.has_throw_for_type('connect'):
            raise Exception('exception:connect')
        return

    def cursor(self):
        if self.has_throw_for_type('cursor'):
            raise Exception('exception:cursor')
        return MockPsycopg2Cursor(self.behaviors)

class TestDbService(unittest.TestCase):
    def setUp(self):
        os.environ['PG_CONNECTION_URI'] = 'psql://guest:guest@localhost:5432/waldo'

    @patch('src.services.db_service.psycopg2')
    def test_connect(self, mock_psql):
        mock_psql.connect.return_value = MockPsycopg2()
        try:
            DbService()
            assert_true(True)
        except:
            assert_true(False)

    @patch('src.services.db_service.psycopg2')
    def test_connect_fails(self, mock_psql):
        mock_psql.connect.side_effect = Exception('exception:connect')
        try:
            DbService()
            assert_true(False)
        except Exception as ex:
            assert_true(str(ex) == 'exception:connect')

    @patch('src.services.db_service.psycopg2')
    def test_execute_sql(self, mock_psql):
        mock_psql.connect.return_value = MockPsycopg2()
        try:
            service = DbService()
            service.execute_sql('test', 1, 2, 3)
            assert_true(True)
        except:
            assert_true(False)

    @patch('src.services.db_service.psycopg2')
    def test_execute_sql_with_response(self, mock_psql):
        expected_data = [1, 2, 3]
        behaviors = { 'fetchall': { 'response': expected_data } }
        mock_psql.connect.return_value = MockPsycopg2(behaviors)
        try:
            service = DbService()
            response = service.execute_sql_with_response('test', 1, 2, 3)
            assert_true(set(expected_data) == set(response))
        except:
            assert_true(False)

    @patch('src.services.db_service.psycopg2')
    def test_fetch_by(self, mock_psql):
        response_set = [('asdf', 'http://www.google.com', 'processing', 'today')]
        behaviors = { 'fetchall': { 'response': response_set } }
        mock_psql.connect.return_value = MockPsycopg2(behaviors)
        try:
            service = DbService()
            response = service.fetch_by('asdf', 'uiop')
            assert_true(isinstance(response, type([])))
            obj = response[0]
            assert_true('uuid' in obj and obj['uuid'] == response_set[0][0])
            assert_true('url' in obj and obj['url'] == response_set[0][1])
            assert_true('status' in obj and obj['status'] == response_set[0][2])
            assert_true('created_at' in obj and obj['created_at'] == response_set[0][3])
        except:
            assert_true(False)

    @patch('src.services.db_service.psycopg2')
    def test_get_by_id(self, mock_psql):
        response_set = [('asdf', 'http://www.google.com', 'processing', 'today')]
        behaviors = { 'fetchall': { 'response': response_set } }
        mock_psql.connect.return_value = MockPsycopg2(behaviors)
        try:
            service = DbService()
            response = service.get_by_id('asdf')
            assert_true(isinstance(response, type({})))
            assert_true('uuid' in response and response['uuid'] == response_set[0][0])
            assert_true('url' in response and response['url'] == response_set[0][1])
            assert_true('status' in response and response['status'] == response_set[0][2])
            assert_true('created_at' in response and response['created_at'] == response_set[0][3])
        except:
            assert_true(False)

    @patch('src.services.db_service.psycopg2')
    def test_get_by_status(self, mock_psql):
        response_set = [('asdf', 'http://www.google.com', 'processing', 'today')]
        behaviors = { 'fetchall': { 'response': response_set } }
        mock_psql.connect.return_value = MockPsycopg2(behaviors)
        try:
            service = DbService()
            response = service.get_by_status('asdf')
            assert_true(isinstance(response, type([])))
            obj = response[0]
            assert_true('uuid' in obj and obj['uuid'] == response_set[0][0])
            assert_true('url' in obj and obj['url'] == response_set[0][1])
            assert_true('status' in obj and obj['status'] == response_set[0][2])
            assert_true('created_at' in obj and obj['created_at'] == response_set[0][3])
        except:
            assert_true(False)

    @patch('src.services.db_service.psycopg2')
    def test_add_thumbnail(self, mock_psql):
        mock_psql.connect.return_value = MockPsycopg2()
        try:
            service = DbService()
            service.add_thumbnail('asdf', 1, 2, '/test.thumb')
            assert_true(True)
        except:
            assert_true(False)

    @patch('src.services.db_service.psycopg2')
    def test_set_status(self, mock_psql):
        mock_psql.connect.return_value = MockPsycopg2()
        try:
            service = DbService()
            service.set_status('asdf', 'completed')
            assert_true(True)
        except:
            assert_true(False)
