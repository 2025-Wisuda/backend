from django.contrib.auth.models import Group


class GroupSeeder:
    @staticmethod
    def seed():
        group_names = [
            "Kepala Laboratorium",
            "Asisten Laboratorium",
            "Teknisi Laboratorium",
            "Dosen",
            "Mahasiswa",
        ]

        for group_name in group_names:
            if not Group.objects.filter(name=group_name).exists():
                Group.objects.create(name=group_name)
                print(f"Group '{group_name}' created")
            else:
                print(f"Group '{group_name}' already exists")
