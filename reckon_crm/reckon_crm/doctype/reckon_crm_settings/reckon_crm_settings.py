from frappe.model.document import Document
from reckon_crm.services.settings import validate_settings


class ReckonCRMSettings(Document):
    def validate(self):
        validate_settings(self)
