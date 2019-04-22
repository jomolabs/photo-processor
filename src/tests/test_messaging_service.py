import os
import json
import pika
import pika.exceptions
import unittest
from unittest.mock import patch
from nose.tools import assert_true
from src.tests.behaviored_mock import BehavioredMock
from src.services.messaging_service import MessagingService, ManagedConnection

class MockPikaChannel(object):
    def __init__(self, behaviors = {}):
        self.is_open = True
        self.behaviors = behaviors

    def queue_declare(self, queue_name, durable=True):
        if 'queue_declare' in self.behaviors and self.behaviors['queue_declare'] == 'throw':
            raise Exception('exception:queue_declare')
        return

    def basic_publish(self, exchange = '', routing_key = '', body = ''):
        if 'basic_publish' in self.behaviors and self.behaviors['basic_publish'] == 'throw':
            raise Exception('exception:basic_publish')
        return

    def consume(self, queue_name):
        if 'consume' in self.behaviors and self.behaviors['consume'] == 'throw':
            raise Exception('exception:consume')
        return ('a', 'b', 'c')

    def close(self):
        return

class MockPikaConnection(object):
    def __init__(self, behaviors = {}):
        self.is_open = True
        self.behaviors = behaviors

    def channel(self):
        if 'channel' in self.behaviors and self.behaviors['channel'] == 'throw':
            raise Exception('exception:channel')
        return MockPikaChannel(self.behaviors)

    def close(self):
        pass

class TestManagedConnection(unittest.TestCase):
    def setUp(self):
        self.connection_string = 'amqp://guest:guest@localhost:5672/%2F'

    @patch('src.services.messaging_service.pika.BlockingConnection')
    def test_init(self, mock_pika):
        mock_pika.return_value = MockPikaConnection()
        try:
            ManagedConnection(self.connection_string)
            mock_pika.assert_called_once()
        except:
            assert_true(False)

        mock_pika.return_value = None
        mock_pika.side_effect = Exception('exception:connect')
        try:
            ManagedConnection(self.connection_string)
            assert_true(False)
        except Exception as ex:
            assert_true(str(ex) == 'exception:connect')

    @patch('src.services.messaging_service.pika.BlockingConnection')
    def test_create_connection(self, mock_pika):
        mock_pika.return_value = MockPikaConnection()
        connection = None
        try:
            connection = ManagedConnection(self.connection_string)
            connection.create_connection(self.connection_string)
        except:
            assert_true(False)
        assert_true(isinstance(connection.connection, MockPikaConnection))

        mock_pika.return_value = None
        mock_pika.side_effect = Exception('exception:create_connection')
        try:
            connection.create_connection(self.connection_string)
            assert_true(False)
        except Exception as ex:
            assert_true(str(ex) == 'exception:create_connection')

    @patch('src.services.messaging_service.pika.BlockingConnection')
    def test_create_channel(self, mock_pika):
        mock_pika.return_value = MockPikaConnection()
        mock_pika.channel.return_value = MockPikaChannel()
        connection = None
        try:
            connection = ManagedConnection(self.connection_string)
            connection.create_channel()
        except:
            assert_true(False)
        assert_true(isinstance(connection.channel, MockPikaChannel))

    @patch('src.services.messaging_service.pika.BlockingConnection')
    def test_create_channel_fails(self, mock_pika):
        behaviors = { 'channel': 'throw' }
        mock_pika.return_value = MockPikaConnection(behaviors)
        mock_pika.channel.return_value = MockPikaChannel(behaviors)
        try:
            connection = ManagedConnection(self.connection_string)
            connection.create_channel()
            assert_true(False)
        except Exception as ex:
            assert_true(str(ex) == 'exception:channel')

    @patch('src.services.messaging_service.pika.BlockingConnection')
    def test_declare(self, mock_pika):
        mock_pika.return_value = MockPikaConnection()
        mock_pika.channel.return_value = MockPikaChannel()
        connection = None
        try:
            connection = ManagedConnection(self.connection_string)
            connection.declare('test')
        except:
            assert_true(False)

    @patch('src.services.messaging_service.pika.BlockingConnection')
    def test_declare_fails(self, mock_pika):
        behaviors = { 'queue_declare': 'throw' }
        mock_pika.return_value = MockPikaConnection(behaviors)
        mock_pika.channel.return_value = MockPikaChannel(behaviors)
        connection = None
        try:
            connection = ManagedConnection(self.connection_string)
            connection.declare('test')
            assert_true(False)
        except Exception as ex:
            assert_true(str(ex) == 'exception:queue_declare')

    @patch('src.services.messaging_service.pika.BlockingConnection')
    def test__with_reconnect_loop(self, mock_pika):
        mock_pika.return_value = MockPikaConnection()
        connection = None
        try:
            connection = ManagedConnection(self.connection_string)
        except Exception as ex:
            assert_true(False)

        def test_okay():
            return True
        try:
            connection._with_reconnect_loop(test_okay)
        except:
            assert_true(False)

        def test_ConnectionClosed():
            raise pika.exceptions.ConnectionClosed(100, 'test')
        try:
            connection._with_reconnect_loop(test_ConnectionClosed)
        except Exception as ex:
            assert_true(isinstance(ex, pika.exceptions.ConnectionClosed))

        def test_ChannelWrongStateError():
            raise pika.exceptions.ChannelWrongStateError()
        try:
            connection._with_reconnect_loop(test_ChannelWrongStateError)
        except Exception as ex:
            assert_true(isinstance(ex, pika.exceptions.ChannelWrongStateError))

        def test_StreamLostError():
            raise pika.exceptions.StreamLostError()
        try:
            connection._with_reconnect_loop(test_StreamLostError)
        except Exception as ex:
            assert_true(isinstance(ex, pika.exceptions.StreamLostError))

class TestMethodFrame(object):
    def __init__(self):
        self.delivery_tag = '1234'

class TestManagedConnectionChannel(BehavioredMock):
    def __init__(self, behaviors = {}):
        super().__init__(behaviors)
        self.was_ack_called = False
        self.was_nack_called = False

    def queue_declare(self, queue_name):
        if self.has_throw_for_type('queue_declare'):
            raise Exception('exception:queue_declare')
        return

    def basic_publish(self, exchange = '', routing_key = '', body = ''):
        if self.has_throw_for_type('basic_publish'):
            raise Exception('exception:basic_publish')
        return

    def consume(self, queue_name):
        if self.has_throw_for_type('consume'):
            raise Exception('exception:consume')
        if self.has_yield_list('consume'):
            for l in self.get_yield_list('consume'):
                yield l
        return ('a', 'b', { 'packet': True })

    def basic_ack(self, delivery_tag):
        self.was_ack_called = True
        if self.has_throw_for_type('basic_ack'):
            raise Exception('exception:basic_ack')
        return

    def basic_nack(self, delivery_tag):
        self.was_nack_called = True
        if self.has_throw_for_type('basic_nack'):
            raise Exception('exception:basic_nack')
        return

class TestManagedConnection(BehavioredMock):
    def __init__(self, behaviors = {}):
        super().__init__(behaviors = behaviors)
        self.channel = TestManagedConnectionChannel(behaviors)

    def declare(self, queue_name):
        if self.has_throw_for_type('declare'):
            raise Exception('declare')
        return

    def _with_reconnect_loop(self, callback):
        if self.has_throw_for_type('_with_reconnect_loop'):
            raise Exception('exception:_with_reconnect_loop')
        callback()

class TestMessagingService(unittest.TestCase):
    def setUp(self):
        self.connection_string = os.environ['AMQP_URI'] = 'amqp://guest:guest@localhost:5672'

    @patch('src.services.messaging_service.ManagedConnection')
    def test_push(self, mock_connection):
        mock_connection.return_value = TestManagedConnection()
        try:
            service = MessagingService()
            service.push({ 'hello': 'world' })
        except:
            assert_true(False)

    @patch('src.services.messaging_service.ManagedConnection')
    def test_push_fails(self, mock_connection):
        behaviors = { 'basic_publish': 'throw' }
        mock_connection.return_value = TestManagedConnection(behaviors)
        try:
            service = MessagingService()
            service.push({ 'hello': 'world' })
            assert_true(False)
        except Exception as ex:
            assert_true(str(ex) == 'exception:basic_publish')

    @patch('src.services.messaging_service.ManagedConnection')
    def test_consume(self, mock_connection):
        behaviors = { 'consume': { 'yield': [] } }
        mock_connection.return_value = TestManagedConnection(behaviors)
        try:
            def nil_callback(parsed):
                return True
            service = MessagingService()
            service.consume(nil_callback)
        except:
            assert_true(False)

    @patch('src.services.messaging_service.ManagedConnection')
    def test_consume_with_data_okay(self, mock_connection):
        behaviors = { 'consume': { 'yield': [(TestMethodFrame(), {}, '{"ok": true}')] } }
        mock_connection.return_value = TestManagedConnection(behaviors)
        try:
            def data_test_callback(parsed):
                return isinstance(parsed, type({})) and 'ok' in parsed and parsed['ok'] == True
            service = MessagingService()
            service.consume(data_test_callback)
            assert_true(mock_connection.channel.was_ack_called)
        except:
            assert_true(False)

    @patch('src.services.messaging_service.ManagedConnection')
    def test_consume_with_data_not_okay(self, mock_connection):
        behaviors = { 'consume': { 'yield': [(TestMethodFrame(), {}, '{"ok": true}')] } }
        mock_connection.return_value = TestManagedConnection(behaviors)
        try:
            def data_test_callback(parsed):
                return isinstance(parsed, type({})) and 'ok' in parsed and parsed['ok'] != True
            service = MessagingService()
            service.consume(data_test_callback)
            assert_true(mock_connection.channel.was_nack_called)
        except:
            assert_true(False)

    @patch('src.services.messaging_service.ManagedConnection')
    def test_consume_fails(self, mock_connection):
        behaviors = { 'consume': 'throw' }
        mock_connection.return_value = TestManagedConnection(behaviors)
        try:
            service = MessagingService()
            service.consume(None)
            assert_true(False)
        except Exception as ex:
            assert_true(str(ex) == 'exception:consume')

if __name__ == '__main__':
    unittest.main()
