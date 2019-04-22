import unittest
from pprint import pprint
from unittest.mock import Mock, patch
from nose.tools import assert_true
from src.services.image_service import ImageService

class MockImageOperator(object):
    def __init__(self, behavior = {}):
        self._behavior = behavior
    def _do_throw(self, method_name):
        return method_name in self._behavior and self._behavior[method_name] is 'throw'
    def thumbnail(self, dimensions, alias_type):
        if self._do_throw('thumbnail'):
            raise Exception('exception:thumbnail')
        return True
    def save(self, output_path, file_extension):
        if self._do_throw('save'):
            raise Exception('exception:save')
        return True

class MockImage(object):
    def __init__(self, behavior = {}):
        self._behavior = behavior
    def _do_throw(self, method_name):
        return method_name in self._behavior and self._behavior[method_name] is 'throw'
    def open(self, path):
        if self._do_throw('open'):
            raise Exception('exception:open')
        return MockImageOperator(self._behavior)

class TestImageService(unittest.TestCase):
    @patch('src.services.image_service.Image')
    def test_success(self, mock_pil):
        mock_pil.return_value = MockImage()
        image_service = ImageService()
        try:
            response = image_service.resize((1,2), '/foo.txt', '/bar.txt')
            assert_true(response is None)
        except:
            assert_true(False)

    @patch('src.services.image_service.Image')
    def test_failure_on_open(self, mock_pil):
        behavior = { 'open': 'throw' }
        mock_pil.return_value = MockImage(behavior)
        mock_pil.open.side_effect = Exception('exception:open')

        image_service = ImageService()
        try:
            response = image_service.resize((1,2), '/foo.txt', '/bar.txt')
            assert_true(False)
        except Exception as ex:
            assert_true(str(ex) == 'exception:open')

    @patch('src.services.image_service.Image')
    def test_failure_on_thumbnail(self, mock_pil):
        behavior = { 'thumbnail': 'throw' }
        mock_pil.return_value = MockImage(behavior)
        mock_pil.open.return_value = MockImageOperator(behavior)

        image_service = ImageService()
        try:
            response = image_service.resize((1,2), '/foo.txt', '/bar.txt')
            assert_true(False)
        except Exception as ex:
            assert_true(str(ex) == 'exception:thumbnail')

    @patch('src.services.image_service.Image')
    def test_failure_on_save(self, mock_pil):
        behavior = { 'save': 'throw' }
        mock_pil.return_value = MockImage(behavior)
        mock_pil.open.return_value = MockImageOperator(behavior)

        image_service = ImageService()
        try:
            response = image_service.resize((1,2), '/foo.txt', '/bar.txt')
            assert_true(False)
        except Exception as ex:
            assert_true(str(ex) == 'exception:save')

if __name__ == '__main__':
    unittest.main()
