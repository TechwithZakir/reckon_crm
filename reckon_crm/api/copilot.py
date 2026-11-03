"""The Sales Agent copilot on a CRM Lead or Deal in /crm. Read-only: it reads the lead and changes nothing.

The copilot itself lives in reckon_sales_agent; this endpoint finds the linked Sales Prospect and asks it. Without the
Sales Agent app installed, the tab says so instead of failing.
"""

import frappe

ALLOWED = ("CRM Lead", "CRM Deal")


def _ok(data: dict) -> dict:
    return {"success": True, "data": data, "message": None}


@frappe.whitelist(methods=["POST"])
def summary(doctype: str, docname: str) -> dict:
    if doctype not in ALLOWED:
        frappe.throw("Invalid request fields.")
    doc = frappe.get_doc(doctype, docname)
    doc.check_permission("read")
    lead = doc.name if doctype == "CRM Lead" else doc.get("lead")
    prospect = frappe.db.get_value("CRM Lead", lead, "rsa_prospect") if lead else None
    if not prospect:
        return _ok({"linked": False})
    try:
        from reckon_sales_agent.api_conversations import copilot_summary
    except ImportError:
        return _ok({"linked": False, "reason": "The Sales Agent app is not installed on this site."})
    return _ok({"linked": True, **copilot_summary(prospect)})
