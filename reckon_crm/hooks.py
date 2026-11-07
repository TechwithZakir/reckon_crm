app_name = "reckon_crm"
app_title = "Reckon CRM"
app_publisher = "Reckon CRM Contributors"
app_description = "Field sales extensions for Frappe CRM"
app_email = ""
app_license = "GPL-3.0-or-later"
required_apps = ["crm", "reckon_saas_platform"]

# Registers Reckon CRM as a SaaS module, the same way Distribution and HRMS do.
reckon_saas_modules = [
    "reckon_crm.saas_module.get_module_definition",
]

from reckon_crm.saas_constants import TENANT_OWNED_DOCTYPES  # noqa: E402

before_install = "reckon_crm.install.check_dependencies"
after_install = "reckon_crm.install.after_install"
after_migrate = "reckon_crm.install.clear_website_cache"
after_uninstall = "reckon_crm.install.clear_website_cache"

# A narrow renderer retains CRM's route resolution, authentication and boot.
# No global path resolver, Desk script injection, or CRM source override.
page_renderer = ["reckon_crm.integrations.crm.renderer.ReckonCRMPage"]

doc_events = {
    "CRM Task": {
        "validate": "reckon_crm.services.task_sync.guard_task",
        "on_trash": "reckon_crm.services.task_sync.guard_task",
    },
    "Event": {
        "validate": "reckon_crm.services.calendar.guard_event",
        "on_trash": "reckon_crm.services.calendar.guard_event",
    },
}

# Company-scoped CRM records: the platform's tenant rules, same as the other SaaS apps.
_tenant_events = {
    doctype: {
        "before_validate": "reckon_crm.tenancy_hooks.bind_company",
        "validate": [
            "reckon_crm.tenancy_hooks.validate_company_immutable",
            "reckon_crm.tenancy_hooks.validate_owned",
        ],
    }
    for doctype in TENANT_OWNED_DOCTYPES
}
for _doctype, _events in _tenant_events.items():
    doc_events.setdefault(_doctype, {}).update(_events)

has_permission = {
    "Reckon CRM Settings": "reckon_crm.services.settings.administrator_permission",
    "CRM Field Visit": "reckon_crm.utils.permissions.document_permission",
    "CRM Customer Location": "reckon_crm.utils.permissions.document_permission",
    **{
        doctype: "reckon_saas_platform.tenant_security.has_tenant_owned_permission"
        for doctype in TENANT_OWNED_DOCTYPES
    },
}
permission_query_conditions = {
    "CRM Field Visit": "reckon_crm.utils.permissions.query_conditions",
    "CRM Customer Location": "reckon_crm.utils.permissions.location_query_conditions",
    **{
        doctype: "reckon_saas_platform.tenant_security.get_tenant_owned_query"
        for doctype in TENANT_OWNED_DOCTYPES
    },
}

# Tenant access follows every assignment (roles, company permission).
doc_events.setdefault("Tenant User Assignment", {}).update({
    "after_insert": "reckon_crm.access.sync_tenant_user_access",
    "on_update": "reckon_crm.access.sync_tenant_user_access",
})

