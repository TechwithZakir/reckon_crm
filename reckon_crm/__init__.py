"""Reckon CRM: extensions for the native Frappe CRM experience."""

__version__ = "0.3.0"

try:
    from reckon_crm.tenant_overrides import apply as _apply_tenant_overrides

    _apply_tenant_overrides()
except ImportError:
    # Outside a bench (for example unit tests) there is no CRM or Frappe to patch.
    pass
