"""
Management command to seed users from JSON data files.

Key Features:
- Loads user data from JSON files (assistant_data.json, staff_data.json, student_data.json)
- Selective seeding by user type (--assistants-only, --staff-only, --students-only)
- Safe clearing of existing users (--clear, preserves superusers)
- Auto-generates usernames from names and ID numbers
- Default password: "password" for all users
"""

import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Command(BaseCommand):
    """Seed users from JSON data with selective options."""

    help = _("Seed users from JSON data files")

    def add_arguments(self, parser):
        """Add command line options for selective seeding."""
        parser.add_argument(
            "--clear",
            action="store_true",
            help=_("Clear existing users before seeding (except superusers)"),
        )
        parser.add_argument(
            "--assistants-only",
            action="store_true",
            help=_("Only seed teaching assistants from JSON data"),
        )
        parser.add_argument(
            "--staff-only",
            action="store_true",
            help=_("Only seed staff users (admin users)"),
        )
        parser.add_argument(
            "--students-only", action="store_true", help=_("Only seed students")
        )
        parser.add_argument(
            "--seed-users-only",
            action="store_true",
            help=_("Only seed users from JSON data"),
        )

    def handle(self, *args, **options):
        """Main seeding logic with selective user type creation."""
        self.stdout.write(
            self.style.SUCCESS(_("🚀 Starting user seeding with JSON data..."))
        )

        # Clear existing users if requested (keep superusers)
        if options["clear"]:
            deleted_count = User.objects.filter(is_superuser=False).delete()[0]
            self.stdout.write(
                self.style.WARNING(
                    _("🗑️ Deleted %d existing users (kept superusers)") % deleted_count
                )
            )

        # Ensure required groups exist
        self.ensure_groups_exist()

        total_created = 0

        if options["seed_users_only"]:
            self.stdout.write(self.style.SUCCESS("🚀 Seeding users only..."))
            created_assistants = self.create_assistants()
            created_staff = self.create_staff()
            created_students = self.create_students()
            total_created = created_assistants + created_staff + created_students
            self.stdout.write(
                self.style.SUCCESS(
                    _(
                        "🎉 Successfully completed user seeding!\n"
                        "📊 Total users created: %d\n"
                        '🔑 All users created with default password: "password"'
                    )
                    % total_created
                )
            )
            return

        # Create assistants if requested
        if not options["staff_only"] and not options["students_only"]:
            created_assistants = self.create_assistants()
            total_created += created_assistants

        # Create staff if requested
        if not options["assistants_only"] and not options["students_only"]:
            created_staff = self.create_staff()
            total_created += created_staff

        # Create students if requested
        if not options["assistants_only"] and not options["staff_only"]:
            created_students = self.create_students()
            total_created += created_students

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                _(
                    "🎉 Successfully completed user seeding!\n"
                    "📊 Total users created: %d\n"
                    '🔑 All users created with default password: "password"'
                )
                % total_created
            )
        )

    def ensure_groups_exist(self):
        """Create required Django groups if they don't exist."""
        groups_data = {
            "Asisten Laboratorium": "Teaching assistants for laboratory",
            "Teknisi Laboratorium": "Laboratory technicians and staff",
            "Mahasiswa": "Students",
            "Dosen": "Lecturers and professors",
            "Kepala Laboratorium": "Laboratory heads",
        }

        for group_name, description in groups_data.items():
            group, created = Group.objects.get_or_create(name=group_name)
            status = "created" if created else "exists"
            self.stdout.write(f'📂 Group "{group_name}" {status}')

    def create_assistants(self):
        """Create teaching assistants from assistant_data.json."""
        self.stdout.write("\n👥 Creating teaching assistants from JSON data...")

        assistants_data = self.load_json_data("assistant_data.json")
        if not assistants_data:
            self.stdout.write(
                self.style.WARNING("⚠️ No assistant data found, skipping...")
            )
            return 0

        assistant_group = Group.objects.get(name="Asisten Laboratorium")
        created_count = 0

        # Process each assistant individually without atomic transaction
        for assistant_data in assistants_data:
            try:
                if self.create_user_from_data(
                    assistant_data,
                    "Asisten Laboratorium",
                    assistant_group,
                    is_staff=True,
                ):
                    created_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Failed to create assistant {assistant_data.get("first_name", "Unknown")}: {str(e)}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(f"✓ Created {created_count} teaching assistants")
        )
        return created_count

    def create_staff(self):
        """Create staff and lecturers from staff_data.json and lecturer_data.json."""
        self.stdout.write("\n🔧 Creating staff users...")

        created_count = 0

        # Create laboratory staff from staff_data.json
        staff_data = self.load_json_data("staff_data.json")
        if staff_data:
            # Create different staff types based on data
            for staff_member in staff_data:
                try:
                    employee_number = staff_member.get("employee_number", "")
                    if employee_number.startswith("KL"):
                        group_name = "Kepala Laboratorium"
                    else:
                        group_name = "Teknisi Laboratorium"

                    group_obj = Group.objects.get(name=group_name)
                    if self.create_user_from_data(
                        staff_member, group_name, group_obj, is_staff=True
                    ):
                        created_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'✗ Failed to create staff {staff_member.get("first_name", "Unknown")}: {str(e)}'
                        )
                    )

        # Create lecturers from lecturer_data.json
        lecturer_data = self.load_json_data("lecturer_data.json")
        if lecturer_data:
            dosen_group = Group.objects.get(name="Dosen")
            for lecturer in lecturer_data:
                try:
                    if self.create_user_from_data(
                        lecturer, "Dosen", dosen_group, is_staff=False
                    ):
                        created_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'✗ Failed to create lecturer {lecturer.get("first_name", "Unknown")}: {str(e)}'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(f"✓ Created {created_count} staff and lecturer users")
        )
        return created_count

    def create_students(self):
        """Create students from student_data.json (generates sample data if file missing)."""
        self.stdout.write("\n🎓 Creating students from JSON data...")

        students_data = self.load_json_data("student_data.json")
        if not students_data:
            # Fallback to generated data if no JSON file
            self.stdout.write(
                self.style.WARNING("⚠️ No student data found, generating sample data...")
            )
            students_data = []
            for i in range(1, 11):  # Create 10 students
                students_data.append(
                    {
                        "first_name": f"Student",
                        "last_name": f"{i:02d}",
                        "student_id": f"23150610{i:02d}",
                    }
                )

        student_group = Group.objects.get(name="Mahasiswa")
        created_count = 0

        # Process each student individually without atomic transaction
        for student_data in students_data:
            try:
                if self.create_user_from_data(
                    student_data, "Mahasiswa", student_group, is_staff=False
                ):
                    created_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Failed to create student {student_data.get("first_name", "Unknown")}: {str(e)}'
                    )
                )

        self.stdout.write(self.style.SUCCESS(f"✓ Created {created_count} students"))
        return created_count

    def create_user_from_data(self, user_data, group_name, group_obj, is_staff=False):
        """
        Create user from data dict with auto-generated username.

        Username format: first_initial.last_name + id_prefix
        Example: j.smith23 (from John Smith with ID starting with 23)

        Returns True if user created, False if skipped (already exists).
        """
        first_name = user_data.get("first_name", "").strip()
        last_name = user_data.get("last_name", "").strip()

        if not first_name or not last_name:
            raise ValueError("First name and last name are required")

        # Generate username from name and ID
        first_initial = first_name[0].lower()
        clean_last_name = slugify(last_name.lower().replace(" ", ""))

        # Use student_id or student_number for students, employee_number for staff
        id_number = (
            user_data.get("student_id")
            or user_data.get("student_number")
            or user_data.get("employee_number", "")
        )

        if id_number:
            id_prefix = id_number[:2] if len(id_number) >= 2 else id_number
            base_username = f"{first_initial}.{clean_last_name}{id_prefix}"
        else:
            base_username = f"{first_initial}.{clean_last_name}"

        # Ensure unique username
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        # Prepare user data
        user_fields = {
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "email": f"{username}@lab.ac.id",
            "group": group_name,
            "is_staff": is_staff,
            "is_active": True,
        }

        # Check if user already exists by student_number or employee_number
        if group_name in ["Asisten Laboratorium", "Mahasiswa"]:
            student_number = user_data.get("student_id") or user_data.get(
                "student_number"
            )
            if (
                student_number
                and User.objects.filter(student_number=student_number).exists()
            ):
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️ User with student number {student_number} already exists, skipping..."
                    )
                )
                return False
            if student_number:
                user_fields["student_number"] = student_number
        elif group_name in ["Kepala Laboratorium", "Teknisi Laboratorium", "Dosen"]:
            employee_number = user_data.get("employee_number")
            if (
                employee_number
                and User.objects.filter(employee_number=employee_number).exists()
            ):
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️ User with employee number {employee_number} already exists, skipping..."
                    )
                )
                return False
            if employee_number:
                user_fields["employee_number"] = employee_number

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f"⚠️ User {username} already exists, skipping...")
            )
            return False

        # Create user
        user = User.objects.create_user(password="password", **user_fields)
        user.groups.add(group_obj)

        self.stdout.write(
            self.style.SUCCESS(f"✓ Created {group_name}: {username} ({user.email})")
        )
        return True

    def load_json_data(self, filename):
        """Load JSON data from management/commands/data/ directory."""
        try:
            # Data files are in the same directory as this command
            data_dir = Path(__file__).parent / "data"
            file_path = data_dir / filename

            if not file_path.exists():
                self.stdout.write(
                    self.style.WARNING(f"⚠️ JSON file not found: {file_path}")
                )
                return []

            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                self.stdout.write(
                    self.style.SUCCESS(f"📄 Loaded {len(data)} records from {filename}")
                )
                return data

        except json.JSONDecodeError as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error parsing JSON file {filename}: {str(e)}")
            )
            return []
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error loading JSON file {filename}: {str(e)}")
            )
            return []
