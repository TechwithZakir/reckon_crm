"""Tenant seed for Reckon CRM. Adds only generic defaults, never another tenant's data."""

from __future__ import annotations


def run_crm_seed(company: str, seed_version: str) -> dict:
    return {"company": company, "seed_version": seed_version, "seeded": []}
