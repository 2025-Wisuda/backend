"""Management command to verify group permissions setup."""

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from core.enums import UserGroup


class Command(BaseCommand):
    help = "Verify that groups have correct permissions assigned"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🔍 Checking group permissions setup..."))

        for group_enum in UserGroup:
            group_name = group_enum.value
            try:
                group = Group.objects.get(name=group_name)
                permissions = group.permissions.all()

                self.stdout.write(f"\n📋 Group: {self.style.WARNING(group_name)}")
                self.stdout.write(f"   Permissions: {len(permissions)}")

                if permissions:
                    for perm in permissions:
                        self.stdout.write(
                            f"   ✅ {perm.content_type.app_label}.{perm.codename}"
                        )
                else:
                    self.stdout.write("   ❌ No permissions assigned")

            except Group.DoesNotExist:
                self.stdout.write(f"❌ Group '{group_name}' not found!")

        self.stdout.write(self.style.SUCCESS("\n✅ Group permissions check completed!"))
