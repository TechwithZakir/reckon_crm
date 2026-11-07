"""Starter CRM masters for a Bangladeshi SME. Pure data, no Frappe import.

CRM Lead Source, Lost Reason and Industry are already populated by Frappe CRM, so only
territories are seeded here. CRM Territory has no Company field, so the starter list is
shared by all tenants and is generic (the eight administrative divisions of Bangladesh).
"""

from __future__ import annotations

TERRITORIES = (
    "Dhaka",
    "Chattogram",
    "Khulna",
    "Rajshahi",
    "Sylhet",
    "Barishal",
    "Rangpur",
    "Mymensingh",
)
