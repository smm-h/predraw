from importlib.metadata import version as _meta_version

try:
    __version__ = _meta_version("predraw")
except Exception:
    __version__ = "unknown"
