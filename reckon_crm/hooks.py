app_name = "reckon_crm"
app_title = "Reckon CRM"
app_publisher = "Reckon CRM Contributors"
app_description = "Field sales extensions for Frappe CRM"
app_email = ""
app_license = "GPL-3.0-or-later"
required_apps = ["crm"]

before_install = "reckon_crm.install.check_dependencies"
after_install = "reckon_crm.install.after_install"
after_migrate = "reckon_crm.install.clear_website_cache"
after_uninstall = "reckon_crm.install.clear_website_cache"

# A narrow renderer retains CRM's route resolution, authentication and boot.
# No global path resolver, Desk script injection, or CRM source override.
page_renderer = ["reckon_crm.integrations.crm.renderer.ReckonCRMPage"]
