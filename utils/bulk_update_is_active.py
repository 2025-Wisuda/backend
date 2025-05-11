def bulk_update_is_active(queryset, active=True):
    rows_updated = queryset.update(is_active=active)
    status = "dipulihkan" if active else "dihapus"
    return f"{rows_updated} jadwal {status}."
