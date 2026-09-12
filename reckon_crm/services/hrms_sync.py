"""Optional HRMS integration: native permissions and validation remain in force."""
import frappe


def sync_log(visit, direction, settings):
    prefix = "checkin" if direction == "IN" else "checkout"
    link = "employee_" + prefix
    if visit.get(link):
        return
    if "hrms" not in frappe.get_installed_apps():
        frappe.throw("HRMS is required for enabled Employee Checkin sync.")
    # Internal lookup is restricted to the validated visit actor, never a client
    # supplied Employee identifier. Do not expose employee data through the API.
    if visit.assigned_to != frappe.session.user:
        frappe.throw("Only the assignee can sync their employee log.", frappe.PermissionError)
    employees = frappe.get_all("Employee", filters={"user_id": visit.assigned_to, "status": "Active"}, pluck="name", limit_page_length=2)
    if len(employees) != 1:
        frappe.throw("Employee sync requires exactly one active Employee linked to your user.")
    log = frappe.new_doc("Employee Checkin")
    log.check_permission("create")
    log.update({"employee": employees[0], "log_type": direction, "time": visit.get(prefix + "_time"),
                "device_id": "Reckon visit " + visit.name, "skip_auto_attendance": settings["skip_auto_attendance"]})
    for axis in ("latitude", "longitude"):
        value = visit.get(prefix + "_" + axis)
        geo_status = visit.get("geo_status" if direction == "IN" else "checkout_geo_status")
        if value is not None and geo_status != "Location Unavailable":
            if not log.meta.has_field(axis):
                frappe.throw("Employee Checkin requires latitude/longitude fields for location sync. Update HRMS.")
            log.set(axis, value)
    log.insert()  # HRMS shift/geofence, duplicate and attendance checks run normally.
    visit.db_set(link, log.name, update_modified=False)
