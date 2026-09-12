from reckon_crm.services.settings import get_settings


def sync_visit(visit, status=None):
    settings = get_settings()
    if settings["sync_calendar"]:
        from reckon_crm.services.calendar import sync_visit as sync_calendar
        sync_calendar(visit, status)
    if settings["sync_tasks"]:
        from reckon_crm.services.task_sync import sync_task
        sync_task(visit, status)
    # The server-only lifecycle action marks the exact transition before save.
    # Do not infer it from get_doc_before_save() in on_update: framework versions
    # differ in when that snapshot remains available.
    direction = visit.flags.get("reckon_employee_direction")
    if not status and settings["sync_employee_checkin"] and direction in ("IN", "OUT"):
        from reckon_crm.services.hrms_sync import sync_log
        sync_log(visit, direction, settings)
