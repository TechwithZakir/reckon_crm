"""Reckon CRM SaaS registration constants. No Frappe import."""

MODULE_KEY = "crm"
MODULE_LABEL = "Reckon CRM"
WORKSPACE = "app/crm"
HOME_ROUTE = "/crm"

ADMIN_ROLE = "Reckon CRM Admin"
USER_ROLE = "Reckon CRM User"
ROLES = (ADMIN_ROLE, USER_ROLE)

MODULE_FEATURES = {"leads": "Leads", "deals": "Deals", "organizations": "Organizations"}

# Company-owned CRM doctypes, scoped to a tenant Company by the platform's rules.
TENANT_OWNED_DOCTYPES = ("CRM Lead", "CRM Deal", "CRM Organization")
