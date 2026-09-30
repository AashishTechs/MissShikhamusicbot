# ==========================================================
# Direct-stream preload compatibility shim.
#
# The active preload implementation lives in helpers/_preload.py.
# This module is kept so older imports do not break.
# ==========================================================

from Elevenyts.helpers._preload import PreloadManager, preload

__all__ = ["PreloadManager", "preload"]
