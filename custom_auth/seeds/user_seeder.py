from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from faker import Faker

fake = Faker()
User = get_user_model()


class UserSeeder:
    @staticmethod
    def seed():
        if not User.objects.filter(username="admin").exists():
            admin = User.objects.create_superuser(
                username="admin", email="admin@gmail.com", password="admin"
            )
            print("Admin user created")
        else:
            print("Admin user already exists")

        if not User.objects.filter(username="kepala_lab").exists():
            kepala_lab = User.objects.create_user(
                username=f"kepala_lab_{fake.unique.user_name()}",
                email=f"kepala_lab_{fake.unique.email()}",
                password="kepala_lab",
                is_staff=True,
            )
            kepala_lab.groups.add(Group.objects.get(name="Kepala Laboratorium"))
            kepala_lab.save()
            print("Kepala Laboratorium user created")
        else:
            print("Kepala Laboratorium user already exists")

        if not User.objects.filter(username="teknisi_lab").exists():
            teknisi_lab = User.objects.create_user(
                username=f"teknisi_lab_{fake.unique.user_name()}",
                email=f"teknisi_lab_{fake.unique.email()}",
                password="teknisi_lab",
                is_staff=True,
            )
            teknisi_lab.groups.add(Group.objects.get(name="Teknisi Laboratorium"))
            teknisi_lab.save()
            print("Teknisi Laboratorium user created")
        else:
            print("Teknisi Laboratorium user already exists")

        for i in range(1, 4):
            username = f"asisten_lab_{i}_{fake.unique.user_name()}"
            if not User.objects.filter(username=username).exists():
                asisten_lab = User.objects.create_user(
                    username=username,
                    email=f"asisten_lab_{i}_{fake.unique.email()}",
                    password=f"asisten_lab_{i}",
                    is_staff=True,
                )
                asisten_lab.groups.add(Group.objects.get(name="Asisten Laboratorium"))
                asisten_lab.save()
                print(f"Asisten Laboratorium {i} user created")
            else:
                print(f"Asisten Laboratorium {i} user already exists")

        for i in range(1, 4):
            username = f"dosen_{i}_{fake.unique.user_name()}"
            if not User.objects.filter(username=username).exists():
                dosen = User.objects.create_user(
                    username=username,
                    email=f"dosen_{i}_{fake.unique.email()}",
                    password=f"dosen_{i}",
                )
                dosen.groups.add(Group.objects.get(name="Dosen"))
                dosen.save()
                print(f"Dosen {i} user created")
            else:
                print(f"Dosen {i} user already exists")

        for i in range(1, 11):
            username = f"mahasiswa_{i}_{fake.unique.user_name()}"
            if not User.objects.filter(username=username).exists():
                mahasiswa = User.objects.create_user(
                    username=username,
                    email=f"mahasiswa_{i}_{fake.unique.email()}",
                    password=f"mahasiswa_{i}",
                )
                mahasiswa.groups.add(Group.objects.get(name="Mahasiswa"))
                mahasiswa.save()
                print(f"Mahasiswa {i} user created")
            else:
                print(f"Mahasiswa {i} user already exists")

        print("Dummy users created and assigned to groups successfully")
