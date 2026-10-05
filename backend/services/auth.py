"""
Stateless bearer-token auth (works across the Vercel -> HF Spaces origin boundary, where
third-party cookies are often blocked), with the Flask session cookie as a fallback.
"""
import functools
import threading
import time
from collections import defaultdict, deque

from flask import current_app, g, jsonify, request, session
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


def _serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='auth-token')


def issue_token(user_id):
    return _serializer().dumps({'uid': user_id})


def _user_from_token():
    header = request.headers.get('Authorization', '')
    if not header.startswith('Bearer '):
        return None
    try:
        data = _serializer().loads(header[7:], max_age=current_app.config['TOKEN_MAX_AGE'])
        return int(data['uid'])
    except (BadSignature, SignatureExpired, KeyError, ValueError):
        return None


def current_user_id():
    return _user_from_token() or session.get('user_id')


def login_required(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        uid = current_user_id()
        if not uid:
            return jsonify({'error': 'Not logged in'}), 401
        g.user_id = uid
        return fn(*args, **kwargs)
    return wrapper


class RateLimiter:
    """Small in-process sliding-window limiter for LLM-backed endpoints."""

    def __init__(self, limit, window_s):
        self.limit, self.window = limit, window_s
        self.hits = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, key):
        now = time.monotonic()
        with self.lock:
            q = self.hits[key]
            while q and now - q[0] > self.window:
                q.popleft()
            if len(q) >= self.limit:
                return False
            q.append(now)
            return True


LLM_LIMITER = RateLimiter(limit=30, window_s=60)


def rate_limited(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if not LLM_LIMITER.allow(getattr(g, 'user_id', request.remote_addr)):
            return jsonify({'error': 'Too many requests, please slow down a little.'}), 429
        return fn(*args, **kwargs)
    return wrapper
