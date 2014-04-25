from __future__ import division
from ajenti.util import public, str_fsize
from itertools import chain, imap
import itertools as it
import datetime as dt
import operator as op
import functools as ft
import chardet

__all__ = ['ident', 'intbool', 'time', 'unixtime', 'timedelta', 'listof', 'dictof', 'ordered', 'compose', 'flip']

def compose(*fs):
    return lambda arg: reduce(lambda a, f: f(a), fs, arg)

def flip(fn):
    return lambda a, b: fn(b, a)

const = lambda c: lambda x: c
ident = lambda x: x

intbool = compose(int, bool)
time = compose(int, ft.partial(flip(divmod), 60), '%2d:%02d'.__mod__)
unixtime = compose(int, dt.datetime.fromtimestamp)
timedelta = compose(int, ft.partial(dt.timedelta, 0))

listof = lambda cast: ft.partial(map, cast)
dictof = lambda cast, key: compose(
        ft.partial(it.imap, cast),
        ft.partial(it.imap, lambda o: (getattr(o, key), o)),
        dict)

ordered = lambda listcast, field: compose(listcast, ft.partial(sorted, key=op.attrgetter(field)))

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
            return dt.datetime.strptime(d, pattern)
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
    _inherit = False

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
        try:
            return self._defaults[key]

        except KeyError:
            if '__' in key:
                names = key.split('__')
                for name in names:
                    try:
                        return getattr(self, name)
                    except AttributeError:
                        continue

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

    def __len__(self):
        return len(self.__dict__.keys())

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, repr(self.__dict__))

    def __iter__(self):
        return self.__dict__.iteritems()

    EMPTY = None
    class __metaclass__(type):
        def __init__(cls, name, bases, attrs):
            casts = {}
            defaults = {}
            keymap = {}

            for base in reversed(bases):
                if getattr(base, '_inherit', True):
                    casts.update(getattr(base, '_casts', {}))
                    defaults.update(getattr(base, '_defaults', {}))
                    keymap.update(getattr(base, '_keymap', {}))

            casts.update(attrs.get('_casts', {}))
            defaults.update(attrs.get('_defaults', {}))
            keymap.update(attrs.get('_keymap', {}))

            if casts:
                attrs.setdefault('_casts', {}).update(casts)
            if defaults:
                attrs.setdefault('_defaults', {}).update(defaults)
            if keymap:
                attrs.setdefault('_keymap', {}).update(keymap)

            type.__init__(cls, name, bases, attrs)

            try:
                cls.EMPTY = cls()
            except AttributeError:
                pass

