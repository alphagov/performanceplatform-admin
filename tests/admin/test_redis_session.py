import unittest
from mock import Mock
from admin.redis_session import RedisSession
from redis import Redis


class RedisSessionTestCase(unittest.TestCase):

    def setUp(self):
        self.redis = Mock(Redis)
        self.prefix = 'admin_app:session:'

    def test_store_session_for_user(self):
        session = RedisSession(
            redis=self.redis, sid='session_id', prefix=self.prefix)
        uid = 'blah'
        session.store_session_for_user(uid)
        self.redis.lpush.assert_called_with(
            '{}user_sessions:{}'.format(self.prefix, uid),
            'session_id'
        )

    def test_delete_sessions_for_user(self):
        sid = 'sid1'
        self.redis.lrange.return_value = [sid]
        session = RedisSession(
            redis=self.redis, sid='session_id', prefix=self.prefix)
        uid = 'blah'
        session.delete_sessions_for_user(uid)
        self.redis.lrange.assert_called_with(
            '{}user_sessions:{}'.format(self.prefix, uid),
            0,
            -1
        )
        self.redis.delete.assert_called_with(
            self.prefix + sid
        )

    def test_delete_sessions_for_user_without_prefix(self):
        sid = 'sid1'
        self.redis.lrange.return_value = [sid]
        session = RedisSession(
            redis=self.redis, sid='session_id')
        uid = 'blah'
        session.delete_sessions_for_user(uid)
        self.redis.lrange.assert_called_with(
            'user_sessions:{}'.format(uid),
            0,
            -1
        )
        self.redis.delete.assert_called_with(
            sid
        )
