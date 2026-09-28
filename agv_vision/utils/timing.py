"""Monotonic step timing with a context-local operation identifier."""

from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from time import perf_counter
from uuid import uuid4


_operation_id = ContextVar('timing_operation_id', default='-')


@contextmanager
def log_step(logger, step):
    """Log elapsed milliseconds on success or failure; preserve exceptions."""
    token = None
    if _operation_id.get() == '-':
        token = _operation_id.set(uuid4().hex[:12])
    started = perf_counter()
    status = 'error'
    try:
        yield
        status = 'ok'
    finally:
        elapsed_ms = (perf_counter() - started) * 1000
        try:
            logger.info(
                '步骤计时 operation_id=%s step=%s status=%s elapsed_ms=%.3f',
                _operation_id.get(), step, status, elapsed_ms,
            )
        finally:
            if token is not None:
                _operation_id.reset(token)


def timed_operation(function):
    """Time a synchronous service method, including nested steps."""
    @wraps(function)
    def wrapped(self, *args, **kwargs):
        with log_step(self.logger, function.__name__):
            return function(self, *args, **kwargs)
    return wrapped
