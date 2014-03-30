from __future__ import division
from ajenti.util import public, str_fsize
from datetime import datetime, timedelta as dt_timedelta
from itertools import chain, imap
import operator as op
import chardet

__all__ = ['ident', 'intbool', 'time', 'unixtime', 'timedelta', 'listof']
const = lambda c: lambda x: c
ident = lambda x: x
intbool = lambda v: bool(int(v))
time = lambda t: '%2d:%02d' % (int(t or 0) / 60, int(t or 0) % 60)
unixtime = lambda t: datetime.fromtimestamp(int(t))
timedelta = lambda t: dt_timedelta(0, int(t))
listof = lambda cast: lambda lst: map(cast, lst)
sort = lambda listcast, field: lambda v: sorted(listcast(v), key=op.attrgetter(field))

FILTERS = {
        'str': str,
        'unicode': unicode,
        'size': str_fsize,
        'date': lambda t: t.strftime('%d %b %Y'),
        'time': lambda t: t.strftime('%H:%M'),
        'datetime': lambda t: t.strftime('%d %b %Y, %H:%M'),
        'percent': lambda v: '%0.2f%%' % (v * 100),
        'truthy': bool,
        'falsy': lambda v: not bool(v),
        }

@public
def fixutf8(value):
    if not value:
        return u''

    try:
        utf8 = value.decode('utf-8')
        raw = utf8.encode('raw_unicode_escape')
        encoding = chardet.detect(raw)['encoding']

        return (utf8 if encoding == 'ascii' else
                raw.decode({
                    'MacCyrillic': 'windows-1251',
                    'ISO-8859-7': 'windows-1251',
                    }.get(encoding, encoding)))

    except (UnicodeDecodeError, UnicodeEncodeError):
        return value


@public
def timestamp(d):
    for pattern in (
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y',
            ):
        try:
            return datetime.strptime(d, pattern)
        except ValueError:
            continue
    return d

@public
def flatten(items):
    return (item
            for _ in items
            for item in _)


@public
def unique(items):
    last_item = next(items)
    yield last_item

    for item in items:
        if item != last_item:
            yield item
            last_item = item

@public
class Model(object):
    _casts = {}
    _defaults = {}
    _keymap = {}
    _filters = FILTERS

    def __init__(self, items=(), **kwargs):
        self.load(items, kwargs)

    def _init(self):
        pass

    def _mapkey(self, key):
        return self._keymap.get(key, None) or key.replace('-', '_')

    def get(self, key, default=None):
        if default is None:
            default = self._defaults.get(key, None)

        return getattr(self, key, default)

    def load(self, *iters, **kwargs):
        if kwargs:
            iters = iters + (kwargs,)

        if iters:
            self.__dict__.update((self._mapkey(k),
                self._casts.get(k, ident)(v) if v is not None else None)
                for it in iters
                for k, v in (it.iteritems() if isinstance(it, dict) else it))

        self._init()

    def _cache(self, key, value):
        setattr(self, key, value)
        return value

    def __getattr__(self, key):
        if '__' in key:
            if '__or__' in key:
                names = key.split('__or__')
                for name in names:
                    try:
                        return getattr(self, name)
                    except AttributeError:
                        continue
                raise AttributeError(key)

            name, filter = key.split('__')
            try:
                return self._filters[filter](getattr(self, name))
            except KeyError:
                if filter == 'exists':
                    return hasattr(self, name)
                elif filter == 'missing':
                    return not hasattr(self, name)
                else:
                    raise AttributeError(key)

        elif key.startswith('is_'):
            name, test = key[3:].rsplit('_', 1)
            return getattr(self, name) == test

        elif key.startswith('isnt_'):
            name, test = key[5:].rsplit('_', 1)
            return getattr(self, name) != test

        try:
            return self._defaults[key]
        except KeyError:
            raise AttributeError(key)

    def update(self, items=(), **kwargs):
        self.__dict__.update(items, **kwargs)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __delitem__(self, key):
        try:
            delattr(self, key)
        except AttributeError:
            pass

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError:
            return self._defaults[key]

    def __contains__(self, key):
        return hasattr(self, key)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, repr(self.__dict__))

    EMPTY = None
    class __metaclass__(type):
        def __init__(cls, name, bases, attrs):
            type.__init__(cls, name, bases, attrs)
            try:
                cls.EMPTY = cls()
            except AttributeError:
                pass

