import django_filters

from ...models import NotificationLogModel


class NotificationLogFilter(django_filters.FilterSet):
    notification_type = django_filters.CharFilter(
        field_name="notification_type", help_text="Filter by notification type"
    )
    is_read = django_filters.BooleanFilter(
        field_name="is_read", help_text="Filter by read status"
    )

    class Meta:
        model = NotificationLogModel
        fields = ["notification_type", "is_read"]
