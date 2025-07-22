from .device_schema import device_list_schema, device_register_schema, device_send_test_schema
from .notification_schema import (
    notification_list_schema,
    notification_mark_as_read_schema,
    notification_mark_all_as_read_schema,
    notification_unread_count_schema,
)

__all__ = [
    "device_list_schema",
    "device_register_schema",
    "device_send_test_schema",
    "notification_list_schema",
    "notification_mark_as_read_schema",
    "notification_mark_all_as_read_schema",
    "notification_unread_count_schema",
]