import frappe
from frappe.model.document import Document

from reckon_crm.utils.geo import coordinates, finite_number
from reckon_crm.utils.permissions import reference_doc


class CRMCustomerLocation(Document):
    def validate(self):
        reference_doc(self.reference_doctype, self.reference_name, "write")
        previous = self.get_doc_before_save()
        if previous:
            reference_doc(previous.reference_doctype, previous.reference_name, "write")
        try:
            self.latitude, self.longitude = coordinates(self.latitude, self.longitude)
            self.geofence_radius = finite_number(self.geofence_radius, "Geofence radius", 1, 10000)
        except ValueError as error:
            frappe.throw(str(error))

    def on_trash(self):
        reference_doc(self.reference_doctype, self.reference_name, "write")
