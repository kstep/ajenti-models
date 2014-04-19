ajenti-models
=============

Ajenti models plugin: bindable models framework for Ajenti templates

Model object is a dict-like object, so it can be bound with `<bind:dict>` tag, as well as with `<binder:context>` tag
or used in collections. Though it is not a true dict (it doesn't inherit from `dict` class).

It can consume raw data on instance creation and normalize them, e.g. make sure some fields are valid numbers
(even if they are provided as strings), or datetimes (in disguise of datetime formatted as string or unix timestamp).
Good live examples are in [transmission][] and [mpd][] plugins.

[transmission]: http://github.com/kstep/ajenti-transmission
[mpd]: http://github.com/kstep/ajenti-mpd

Also it supports some syntax sugar in templates: you can use `<label bind="field1__field2__field3" />` syntax to show 
first non-empty field available. E.g. `<label bind="title__name" />` will bind model's title field if it's present,
or name field otherwise.

If field is missing from model's input, it's value can be taken from `_defaults` class property.
It can also normalize key names with either mappings from `_keymap` class property or by overriding `_mapkey()`
method for complex cases. By default all fields are cast to lower case and converted to word_separated_with_underscores
format from CamelCaseFormat.

Example:

```python
from ajenti.plugins.models.api import *

@public
class Song(Model):
    _casts = {
            'date': timestamp,
            'last_modified': timestamp,
            'pos': int,
            'id': int,
            'time': timedelta,
            'genre': lambda g: ', '.join(set(g)) if isinstance(g, list) else g,

            'title': fixutf8,
            'album': fixutf8,
            'artist': fixutf8,
            }
    _defaults = {
            'time': None,
            }

    def _init(self):
        if 'name' in self:
            self.time = u'\u221E'
            self.icon = 'signal'
            self.is_stream = True

        elif 'title' in self:
            self.icon = 'music'
            self.is_stream = False
```
