import unittest
from unittest.mock import Mock, patch
from nose.tools import assert_true
from src.services.fetch_service import FetchService

class MockUrllibRequest(object):
    def __init__(self, behavior = {}):
        self._behavior = behavior
    def _do_throw(self, method_name):
        return method_name in self._behavior and self._behavior[method_name] is 'throw'
    def urlretrieve(self, path):
        if self._do_throw('urlretrieve'):
            raise Exception('exception:urlretrieve')

class TestFetchService(unittest.TestCase):
    @patch('src.services.fetch_service.urllib.request')
    def test_success(self, mock_urllib_request):
        mock_urllib_request.return_value = MockUrllibRequest()
        fetch_service = FetchService()
        try:
            response = fetch_service.download('www.google.com', '/test.txt')
            assert_true(response is None)
        except:
            assert_true(False)

    @patch('src.services.fetch_service.urllib.request')
    def test_failure(self, mock_urllib_request):
        mock_urllib_request.return_value = MockUrllibRequest()
        mock_urllib_request.urlretrieve.side_effect = Exception('exception:urlretrieve')
        fetch_service = FetchService()
        try:
            fetch_service.download('www.google.com', '/test.txt')
            assert_true(False)
        except Exception as ex:
            assert_true(str(ex) == 'exception:urlretrieve')

if __name__ == '__main__':
    unittest.main()
