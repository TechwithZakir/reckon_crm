import frappe
from reckon_crm.services.calendar import event_values

TASK_TOKEN = object()


def sync_task(visit, status=None):
    values = event_values(visit, status)
    state = status or visit.status
    name = visit.get("crm_task")
    task = frappe.get_doc("CRM Task", name, for_update=True) if name else frappe.new_doc("CRM Task")
    task.update({"title": f"Visit: {visit.reference_name}"[:140], "description": values["description"],
        "assigned_to": visit.assigned_to, "due_date": values["ends_on"],
        "reference_doctype": visit.reference_doctype, "reference_docname": visit.reference_name,
        "status": {"Started":"In Progress", "Completed":"Done", "Cancelled":"Canceled", "Missed":"Canceled"}.get(state, "Todo"),
        "priority": "Medium"})
    if task.meta.has_field("start_date"):
        task.start_date = visit.planned_date
    options = (task.meta.get_field("status").options or "").splitlines()
    if task.status not in options:
        frappe.throw("Installed CRM Task status options are incompatible with visit sync.")
    task.flags.reckon_task_sync = TASK_TOKEN
    if name:
        # Server-owned link is protected by visit validation; visitor may not own
        # the manager-created task. Native Task validation/assignment still runs.
        task.save(ignore_permissions=True)
    else:
        task.insert()
        visit.db_set("crm_task", task.name, update_modified=False)


def guard_task(task, method=None):
    if task.flags.get("reckon_task_sync") is TASK_TOKEN:
        return
    if frappe.db.has_column("CRM Field Visit", "crm_task") and frappe.db.exists("CRM Field Visit", {"crm_task": task.name}):
        frappe.throw("This task is managed by a field visit. Change the visit instead.")
