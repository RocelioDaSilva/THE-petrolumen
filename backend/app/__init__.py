"""PetroLúmen application package.

Places the vendored third-party packages in ``backend/vendor`` on ``sys.path``
so imports such as ``import ppes`` resolve from the repository rather than from
a machine-local editable install.
"""

from __future__ import annotations

import os
import sys

_VENDOR_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vendor")
if os.path.isdir(_VENDOR_DIR) and _VENDOR_DIR not in sys.path:
    sys.path.insert(0, _VENDOR_DIR)
