# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

"""Guard the public RadioTV shortcut contract without importing NVDA."""

import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class GlobalShortcutTests(unittest.TestCase):
    def test_five_distinct_global_gestures_use_the_radiotv_modifier_family(self):
        tree = ast.parse((ROOT / "globalPlugins/radiotv/nvda_plugin.py").read_text(encoding="utf-8"))
        gestures = [keyword.value.value.casefold() for node in ast.walk(tree)
                    if isinstance(node, ast.Call) for keyword in node.keywords
                    if keyword.arg == "gesture" and isinstance(keyword.value, ast.Constant)]
        self.assertEqual(5, len(gestures))
        self.assertEqual(5, len(set(gestures)))
        keys = set()
        for gesture in gestures:
            self.assertTrue(gesture.startswith("kb:"))
            parts = gesture.removeprefix("kb:").split("+")
            self.assertEqual({"windows", "alt"}, set(parts[:-1]))
            keys.add(parts[-1])
        self.assertEqual({"v", "p", "s", "uparrow", "downarrow"}, keys)


if __name__ == "__main__":
    unittest.main()
