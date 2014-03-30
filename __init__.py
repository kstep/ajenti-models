from ajenti.api import *  # noqa
from ajenti.plugins import *  # noqa

info = PluginInfo(
    title='Models',
    icon=None,
    dependencies=[
    ],
)

def init():
    import api
