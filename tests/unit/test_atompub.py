import functools
import unittest

import httplib2
import stubout

import yagi.config

from yagi.handler.atompub_handler import AtomPub


class MockResponse(object):
    def __init__(self, status_code=200):
        self.status = status_code


class AtomPubTests(unittest.TestCase):
    """Tests to ensure the ATOM Pub code holds together as expected"""

    def setUp(self):
        self.stubs = stubout.StubOutForTesting()
        config_dict = {
            'atompub': {
                'url': 'http://127.0.0.1:9000/test/%(event_type)s',
                'user': 'user',
                'key': 'key',
                'interval': 30,
                'max_wait': 600,
                'retries': 1,
                'failures_before_reauth': 5
            },
            'event_feed': {
                'feed_title': 'feed_title',
                'feed_host': 'feed_host',
                'use_https': False,
                'port': 'port'
            },
            'handler_auth': {
                'method': 'no_auth'
            }
        }

        self.handler = AtomPub()

        def get(*args, **kwargs):
            val = None
            for arg in args:
                if val:
                    val = val.get(arg)
                else:
                    val = config_dict.get(arg)
                    if not val:
                        return None or kwargs.get('default')
            return val

        def config_with(*args):
            return functools.partial(get, args)

        self.stubs.Set(yagi.config, 'config_with', config_with)
        self.stubs.Set(yagi.config, 'get', get)

    def tearDown(self):
        self.stubs.UnsetAll()

    def test_notify(self):
        messages = [{'event_type': 'instance_create',
                    'message_id': 1,
                    'content': dict(a=3)}]

        def gen():
            return messages

        self.called = False

        def mock_request(*args, **kwargs):
            self.called = True
            return MockResponse(201), None

        self.stubs.Set(httplib2.Http, 'request', mock_request)
        self.handler.handle_messages(gen)
        self.assertEqual(self.called, True)

    def test_notify_fails(self):
        messages = [{'event_type': 'instance_create',
                     'message_id': 1,
                     'content': dict(a=3)}]
        self.called = False

        def mock_request(*args, **kwargs):
            self.called = True
            return MockResponse(404), None

        def gen():
            return messages

        self.stubs.Set(httplib2.Http, 'request', mock_request)
        self.handler.handle_messages(gen)
        self.assertEqual(self.called, True)
