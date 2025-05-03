def bulk_update_is_active(queryset, active=True):
    rows_updated = queryset.update(is_active=active)
    status = (
        "dipulihkan (ditandai aktif)" if active else "dihapus (ditandai tidak aktif)"
    )
    return f"{rows_updated} jadwal {status}."
