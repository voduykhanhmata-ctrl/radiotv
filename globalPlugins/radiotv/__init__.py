# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh
"""RadioTV package boundary.

The core package is importable by tests and maintenance tools that run outside
NVDA. NVDA-specific modules are loaded only when the NVDA runtime is present.
"""

try:
    import globalPluginHandler as _nvda_runtime_probe
except ImportError:
    pass
else:
    from .nvda_plugin import GlobalPlugin

    __all__ = ("GlobalPlugin",)
