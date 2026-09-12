from reckon_crm.services.settings import get_settings


def sync_visit(visit, status=None):
    settings = get_settings()
    if settings["sync_calendar"]:
        from reckon_crm.services.calendar import sync_visit as sync_calendar
        sync_calendar(visit, status)
    if settings["sync_tasks"]:
        from reckon_crm.services.task_sync import sync_task
        sync_task(visit, status)
    # HRMS logs are generated only at the actual transition, never retroactively
    # on an ordinary save or when settings are enabled later.
    previous = visit.get_doc_before_save()
    if not status and settings["sync_employee_checkin"] and previous and previous.status != visit.status:
        from reckon_crm.services.hrms_sync import sync_log
        if visit.status == "Started":
            sync_log(visit, "IN", settings)
        elif visit.status == "Completed":
            sync_log(visit, "OUT", settings)
