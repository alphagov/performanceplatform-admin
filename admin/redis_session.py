import pickle
from datetime import timedelta
from uuid import uuid4
from redis import Redis
from werkzeug.datastructures import CallbackDict
from flask.sessions import SessionInterface, SessionMixin
import logging
# see http://flask.pocoo.org/snippets/75/


class RedisSession(CallbackDict, SessionMixin):

    def __init__(
            self, redis=None, initial=None, sid=None, new=False, prefix=''):
        def on_update(self):
            self.modified = True
        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.new = new
        self.modified = False
        self.redis = redis
        self.logger = logging.getLogger(__name__)
        self.prefix = prefix

    def store_session_for_user(self, uid):
        """ Associate the current session with the given uid

        Used for later destroying those sessions when reauthing with signon
        uid - a signon user_id
        """
        self.logger.debug(
            'saving session id {} for user {} to redis'.format(self.sid, uid)
        )
        self.redis.lpush(
            '{}user_sessions:{}'.format(self.prefix, uid),
            self.sid,
        )

    def delete_sessions_for_user(self, uid):
        """ Delete all sessions for a user with given uid

        uid - a signon user_id
        """
        self.logger.debug('deleting sessions for {}'.format(uid))
        session_ids = self.redis.lrange(
            '{}user_sessions:{}'.format(self.prefix, uid),
            0,
            -1
        )
        for sid in session_ids:
            self.logger.debug('signing out {}'.format(sid))
            self.redis.delete('{}{}'.format(self.prefix, sid))


class RedisSessionInterface(SessionInterface):
    serializer = pickle
    session_class = RedisSession

    def __init__(self, redis=None, prefix=''):
        if redis is None:
            redis = Redis()
        self.redis = redis
        self.prefix = prefix + 'session:'

    def generate_sid(self):
        return str(uuid4())

    def get_redis_expiration_time(self, app, session):
        if session.permanent:
            return app.permanent_session_lifetime
        return timedelta(days=1)

    def open_session(self, app, request):
        sid = request.cookies.get(app.session_cookie_name)
        if not sid:
            sid = self.generate_sid()
            return self.session_class(
                redis=self.redis, sid=sid, new=True, prefix=self.prefix)
        val = self.redis.get(self.prefix + sid)
        if val is not None:
            data = self.serializer.loads(val)
            return self.session_class(
                redis=self.redis, initial=data, sid=sid, prefix=self.prefix)
        return self.session_class(
            redis=self.redis, sid=sid, new=True, prefix=self.prefix)

    def save_session(self, app, session, response):
        domain = self.get_cookie_domain(app)
        if not session:
            self.redis.delete(self.prefix + session.sid)
            if session.modified:
                response.delete_cookie(app.session_cookie_name,
                                       domain=domain)
            return
        redis_exp = self.get_redis_expiration_time(app, session)
        cookie_exp = self.get_expiration_time(app, session)
        val = self.serializer.dumps(dict(session))
        self.redis.setex(self.prefix + session.sid, val,
                         int(redis_exp.total_seconds()))
        response.set_cookie(app.session_cookie_name, session.sid,
                            expires=cookie_exp, httponly=True,
                            domain=domain)
