# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

import ast
import pathlib
import runpy
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class PackageStructureTests(unittest.TestCase):

    def test_all_python_files_parse(self):
        for path in self.project_code_files():
            if path.suffix != ".py":
                continue
            with self.subTest(path=path.relative_to(ROOT)):
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    def test_required_runtime_and_help_files_exist(self):
        required = (
            ROOT / "manifest.ini",
            ROOT / "LICENSE",
            ROOT / "LICENSING.md",
            ROOT / "THIRD_PARTY_NOTICES.md",
            ROOT / "doc" / "vi" / "readme.html",
            ROOT / "doc" / "en" / "readme.html",
            ROOT / "globalPlugins" / "radiotv" / "runtime" / "x64" / "bass.dll",
            ROOT / "globalPlugins" / "radiotv" / "runtime" / "x64" / "basshls.dll",
            ROOT / "globalPlugins" / "radiotv" / "runtime" / "x86" / "bass.dll",
            ROOT / "globalPlugins" / "radiotv" / "runtime" / "x86" / "basshls.dll",
        )
        self.assertTrue(all(path.is_file() for path in required))

    def test_runtime_excludes_unapproved_or_legacy_plugins(self):
        allowed = {"bass.dll", "basshls.dll"}
        for architecture in ("x64", "x86"):
            runtime_dir = ROOT / "globalPlugins" / "radiotv" / "runtime" / architecture
            files = {path.name.lower() for path in runtime_dir.iterdir() if path.is_file()}
            self.assertEqual(allowed, files)
        forbidden_names = {"ffmpeg.exe", "bass_aac.dll", "bass_fx.dll", "bassmix.dll"}
        project_files = {path.name.lower() for path in (ROOT / "globalPlugins").rglob("*") if path.is_file()}
        self.assertTrue(forbidden_names.isdisjoint(project_files))

    def test_manifest_declares_the_source_release_version(self):
        manifest = (ROOT / "manifest.ini").read_text(encoding="utf-8")
        self.assertIn("version = 0.1.0", manifest)
        self.assertIn("license = LGPL-2.1-or-later", manifest)
        self.assertNotIn("updateChannel", manifest)

    def test_project_files_declare_the_new_license(self):
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("GNU LESSER GENERAL PUBLIC LICENSE", license_text)
        self.assertIn("Version 2.1", license_text)
        for path in self.project_code_files():
            with self.subTest(path=path.relative_to(ROOT)):
                first_line = path.read_text(encoding="utf-8").splitlines()[0]
                self.assertEqual(
                    "# SPDX-License-Identifier: LGPL-2.1-or-later",
                    first_line,
                )

    @staticmethod
    def project_code_files():
        return [path for folder in ("globalPlugins", "tests", "tools")
                for path in (ROOT / folder).rglob("*")
                if path.suffix in (".py", ".ps1")]

    def test_sport_category_is_presented_as_football(self):
        main_window = (
            ROOT / "globalPlugins" / "radiotv" / "ui" / "main_window.py"
        ).read_text(encoding="utf-8")
        self.assertIn('"sport": "Bóng đá"', main_window)
        self.assertNotIn('"sport": "Thể thao"', main_window)

    def test_unsupported_source_inventory_is_not_packaged(self):
        build_module = runpy.run_path(str(ROOT / "tools" / "build_dev_package.py"))
        archive_names = {
            build_module["archive_name"](path)
            for path in build_module["iter_package_files"]()
        }
        self.assertNotIn("data/tv_sources_unsupported.json", archive_names)
        self.assertNotIn("data/football_sources_unsupported.json", archive_names)


if __name__ == "__main__":
    unittest.main()
