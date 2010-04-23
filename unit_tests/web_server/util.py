import uuid
import itertools

from diyapi_web_server.amqp_handler import AMQPHandler


class FakeMessage(object):
    def __init__(self, routing_key, body, request_id=None):
        self.routing_key = routing_key
        self.body = body
        if request_id is not None:
            self.request_id = request_id

    def marshall(self):
        return self.body


class MockChannel(object):
    """Stand in for AMQP channel that records published messages."""
    def __init__(self):
        self.messages = []

    def basic_publish(self, *args, **kwargs):
        self.messages.append((args, kwargs))


class FakeAMQPHandler(AMQPHandler):
    """An AMQPHandler that sends replies itself."""
    def __init__(self):
        super(FakeAMQPHandler, self).__init__()
        self.replies_to_send = {}

    def send_message(self, message, exchange=None):
        replies = super(FakeAMQPHandler, self).send_message(message, exchange)
        for reply in self.replies_to_send.get(message.request_id, ()):
            replies.put(reply)
        return replies


def fake_uuid_gen():
    for i in itertools.count():
        yield uuid.UUID(int=i)


class MockSqlCursor(object):
    def __init__(self):
        self.rows = {}
        self.queries = []
        self.results = None

    def execute(self, query, args=()):
        self.queries.append((query, args))
        try:
            self.results = list(self.rows[(query, tuple(args))])
        except KeyError:
            self.results = None

    def fetchone(self):
        if self.results:
            return self.results[0]
        return None

    def fetchall(self):
        return self.results


class MockSqlConnection(object):
    def __init__(self):
        self._cursor = MockSqlCursor()

    def cursor(self):
        return self._cursor


def fake_time():
    return 12345.123


class FakeAuthenticator(object):
    def __init__(self, remote_user):
        self.remote_user = remote_user

    def _get_key_id(self, username):
        # TODO: remove this when application is fixed
        return 0

    def authenticate(self, req):
        if self.remote_user is not None:
            req.remote_user = self.remote_user
            return True
        return False