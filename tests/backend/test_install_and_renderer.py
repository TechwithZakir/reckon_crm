"""Fast adapter contract tests; no live Frappe/site/database implied."""

import importlib
import hashlib
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


class AdapterContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.frappe = types.ModuleType("frappe")
        self.frappe.conf = {}
        self.frappe.__version__ = "15.0.0"
        self.frappe.get_installed_apps = Mock(return_value=["frappe", "crm"])
        self.frappe.get_hooks = Mock(return_value=[
            "reckon_crm.integrations.crm.renderer.ReckonCRMPage"
        ])
        self.frappe.get_app_path = lambda app, *parts: str(self.root.joinpath(app, *parts))
        self.frappe.throw = Mock(side_effect=RuntimeError("dependency error"))
        self.frappe.render_template = Mock(return_value="<html>CRM</html>")
        self.context = Mock(return_value={"boot": {"csrf_token": "test-token"}})
        crm_page = types.ModuleType("crm.www.crm")
        crm_page.get_context = self.context
        self.modules = patch.dict(sys.modules, {"frappe": self.frappe, "crm.www.crm": crm_page})
        self.modules.start()
        self.addCleanup(self.modules.stop)
        from reckon_crm import install
        from reckon_crm.integrations.crm import renderer

        self.install = importlib.reload(install)
        self.renderer = importlib.reload(renderer)
        from reckon_crm import diagnostics

        self.diagnostics = importlib.reload(diagnostics)

    def write_template(self):
        target = self.root / "reckon_crm" / "templates" / "reckon_crm.html"
        target.parent.mkdir(parents=True)
        target.write_text("{{ boot }}", encoding="utf-8")
        assets = self.root / "reckon_crm" / "public" / "frontend" / "abc123"
        assets.mkdir(parents=True)
        (assets / "index.html").write_text("assets", encoding="utf-8")
        # Mirror frappe.get_app_path('crm').parent / 'frontend' in this isolated tree.
        source = self.root / "frontend"
        source.mkdir(parents=True, exist_ok=True)
        files = {}
        for index in range(6):
            filename = f"source{index}.js"
            (source / filename).write_bytes(b"source")
            files[filename] = hashlib.sha256(b"source").hexdigest()
        target.with_suffix(".json").write_text(json.dumps({"schema": 1, "buildId": "abc123", "files": files}))

    def test_requires_crm_but_not_optional_apps(self):
        for version in ["15.0.0", "16.0.0", "17.0.0-dev"]:
            self.frappe.__version__ = version
            self.install.check_dependencies()
        self.frappe.get_installed_apps.return_value = ["frappe"]
        with self.assertRaises(RuntimeError):
            self.install.check_dependencies()

    def test_old_framework_rejected(self):
        self.frappe.__version__ = "14.0.0"
        with self.assertRaises(RuntimeError):
            self.install.check_dependencies()

    def test_missing_template_and_disabled_extension_fall_back(self):
        page = self.renderer.ReckonCRMPage("crm")
        self.assertFalse(page.can_render())
        self.write_template()
        self.assertTrue(page.can_render())
        self.frappe.conf["reckon_crm_disabled"] = True
        self.assertFalse(page.can_render())

    def test_other_pages_untouched(self):
        self.write_template()
        for route in ["app", "desk", "login", "crm-form", "api/method/test"]:
            self.assertFalse(self.renderer.ReckonCRMPage(route).can_render())

    def test_stale_or_missing_assets_fall_back(self):
        self.write_template()
        page = self.renderer.ReckonCRMPage("crm")
        self.assertTrue(page.can_render())
        metadata = page.template_path.with_suffix(".json")
        data = json.loads(metadata.read_text())
        data["files"][next(iter(data["files"]))] = "old"
        metadata.write_text(json.dumps(data))
        self.assertFalse(page.can_render())
        metadata.write_text("broken json")
        self.assertFalse(page.can_render())

    def test_authentication_and_boot_delegated_and_response_not_cached(self):
        self.write_template()
        response = self.renderer.ReckonCRMPage("crm").render()
        self.context.assert_called_once_with()
        self.frappe.render_template.assert_called_once_with("{{ boot }}", self.context.return_value)
        self.assertIn("no-store", response.headers["Cache-Control"])
        self.context.side_effect = PermissionError("CRM access denied")
        with self.assertRaises(PermissionError):
            self.renderer.ReckonCRMPage("crm").render()

    def test_diagnostics_explain_missing_site_prerequisites_and_hooks(self):
        self.frappe.get_installed_apps.return_value = ["frappe"]
        self.assertIn("Frappe CRM", self.diagnostics.status()["reason"])
        self.frappe.get_installed_apps.return_value = ["frappe", "crm"]
        self.assertIn("not installed", self.diagnostics.status()["reason"])
        self.frappe.get_installed_apps.return_value = ["frappe", "crm", "reckon_crm"]
        self.frappe.get_hooks.return_value = None
        self.assertIn("hook is missing", self.diagnostics.status()["reason"])

    def test_diagnostics_distinguish_unbuilt_ready_and_disabled(self):
        self.frappe.get_installed_apps.return_value = ["frappe", "crm", "reckon_crm"]
        state = self.diagnostics.status()
        self.assertFalse(state["ready"])
        self.assertIn("not been built", state["reason"])
        self.assertEqual(state["build_command"], "bench build --app reckon_crm")
        self.write_template()
        state = self.diagnostics.status()
        self.assertTrue(state["ready"])
        self.assertEqual(state["url"], "/crm/visits")
        self.frappe.conf["reckon_crm_disabled"] = 1
        state = self.diagnostics.status()
        self.assertFalse(state["ready"])
        self.assertIn("enable_command", state)
        self.assertNotIn("build_command", state)

    def test_diagnostics_identify_stale_and_missing_build_files(self):
        self.write_template()
        page = self.renderer.ReckonCRMPage("crm")
        source = self.root / "frontend" / "source0.js"
        source.write_bytes(b"updated")
        self.assertIn("source0.js", page.asset_status()["reason"])
        source.write_bytes(b"source")
        (self.root / "reckon_crm/public/frontend/abc123/index.html").unlink()
        self.assertIn("asset directory is missing", page.asset_status()["reason"])

    def test_install_reports_frontend_activation(self):
        with patch.object(self.install, "clear_website_cache"), patch("builtins.print") as output:
            self.install.after_install()
            self.assertIn("frontend is inactive", output.call_args_list[0].args[0])
            self.assertIn("bench build", output.call_args_list[1].args[0])
            self.write_template()
            output.reset_mock()
            self.install.after_install()
            self.assertIn("/crm/visits", output.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
