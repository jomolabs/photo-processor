import sys
import os
import time
import pika, pika.exceptions
import json
import threading

class ManagedConnection(object):
    def __init__(self, connection_string):
        self.lock = threading.Lock()
        self.connection_string = connection_string
        self.connection = None
        self.channel = None
        self.connect()

    def connect(self):
        self.lock.acquire(blocking=True)
        try:
            for closeable in [self.channel, self.connection]:
                if closeable is not None and closeable.is_open:
                    try:
                        closeable.close()
                    except Exception:
                        pass
            self.create_connection(self.connection_string)
            self.create_channel()
        except Exception as e:
            raise e
        finally:
            self.lock.release()

    def create_connection(self, connection_string):
        self.connection = pika.BlockingConnection(pika.URLParameters(connection_string))

    def create_channel(self):
        self.channel = self.connection.channel()

    def declare(self, queue_name):
        def _declare():
            self.channel.queue_declare(queue_name, durable=True)
        self._with_reconnect_loop(_declare)

    def _with_reconnect_loop(self, callback):
        retries = 0
        while True:
            try:
                callback()
                break
            except (pika.exceptions.ConnectionClosed, pika.exceptions.ChannelWrongStateError, pika.exceptions.StreamLostError) as ex:
                retries += 1
                if retries == 3:
                    raise ex
                time.sleep(1)
                self.connect()
            except Exception as ex:
                raise ex

class MessagingService(object):
    def __init__(self):
        self.queue_name = 'photo-processor'
        self.socket = ManagedConnection(os.environ['AMQP_URI'])
        self.socket.declare(self.queue_name)

    def push(self, msg):
        def _send():
            self.socket.channel.basic_publish(exchange='', routing_key=self.queue_name, body=json.dumps(msg))
        self.socket._with_reconnect_loop(_send)

    def consume(self, callback):
        def _consume():
            for method_frame, properties, body in self.socket.channel.consume(self.queue_name):
                parsed = json.loads(body)
                if callback(parsed) == True:
                    self.socket.channel.basic_ack(method_frame.delivery_tag)
                else:
                    self.socket.channel.basic_nack(method_frame.delivery_tag)
        self.socket._with_reconnect_loop(_consume)
