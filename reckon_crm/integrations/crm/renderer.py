"""Serve the additive CRM build, falling back to CRM when not built/disabled."""

from pathlib import Path
import hashlib
import json

import frappe
from werkzeug.wrappers import Response


class ReckonCRMPage:
    def __init__(self, path, http_status_code=None):
        self.path = path.strip("/")
        self.http_status_code = http_status_code or 200

    def can_render(self):
        # CRM's existing website rule resolves /crm/* to the endpoint `crm`.
        return (
            self.path == "crm"
            and not frappe.conf.get("reckon_crm_disabled")
            and self.template_path.is_file()
            and self.assets_match_source()
        )

    def assets_match_source(self):
        return self.asset_status()["ready"]

    def asset_status(self):
        """A CRM update must not silently continue serving an obsolete adapter build."""
        def result(ready, reason):
            return {"ready": ready, "reason": reason}

        if frappe.conf.get("reckon_crm_disabled"):
            return result(False, "Reckon CRM is disabled by reckon_crm_disabled in site configuration.")
        if not self.template_path.is_file():
            return result(False, "Reckon frontend has not been built: the generated HTML template is missing.")
        try:
            metadata = json.loads(self.template_path.with_suffix(".json").read_text(encoding="utf-8"))
            build_id = metadata["buildId"]
            if not isinstance(build_id, str) or not build_id or not all(c in "0123456789abcdef-" for c in build_id):
                return result(False, "The frontend build ID is invalid; rebuild Reckon CRM.")
            assets = Path(frappe.get_app_path("reckon_crm", "public", "frontend", build_id))
            if not (assets / "index.html").is_file():
                return result(False, "The generated frontend asset directory is missing; rebuild Reckon CRM.")
            source = Path(frappe.get_app_path("crm")).parent / "frontend"
            files = metadata["files"]
            if metadata.get("schema") != 1 or not isinstance(files, dict) or len(files) != 6:
                return result(False, "The frontend compatibility metadata is invalid; rebuild Reckon CRM.")
            for filename, expected in files.items():
                target = (source / filename).resolve()
                if not target.is_relative_to(source.resolve()):
                    return result(False, "The frontend compatibility metadata contains an invalid source path.")
                if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
                    return result(False, f"CRM source changed since the Reckon build: {filename}. Rebuild Reckon CRM.")
            return result(True, "Reckon frontend assets match the installed CRM source.")
        except (OSError, ValueError, KeyError, TypeError):
            return result(False, "Frontend metadata or CRM source is missing, unreadable, or invalid; rebuild Reckon CRM.")

    @property
    def template_path(self):
        return Path(frappe.get_app_path("reckon_crm", "templates", "reckon_crm.html"))

    def render(self):
        from crm.www.crm import get_context

        # Never generate boot independently: upstream enforces CRM access and redirects.
        context = get_context()
        html = frappe.render_template(self.template_path.read_text(encoding="utf-8"), context)
        return Response(
            html,
            status=self.http_status_code,
            mimetype="text/html",
            headers={"Cache-Control": "no-store, private"},
        )
