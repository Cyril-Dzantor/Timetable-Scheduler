from django.core.management.base import BaseCommand
from Timetable.models import RoomType, LabType, CourseType

class Command(BaseCommand):
    help = 'Loads Room Types, Lab Types, and Course Types from our dataset'

    def handle(self, *args, **kwargs):
        # Room Types (adjusted per your request)
        room_types = [
            {'name': 'Lecture Hall', 'description': 'Large room for lectures'},
            {'name': 'Classroom', 'description': 'Standard teaching room'},
            {'name': 'Laboratory', 'description': 'Room for practical experiments'},
            {'name': 'Auditorium', 'description': 'Large capacity event space'},
        ]

        # Your exact Lab Types
        lab_types = [
            {'name': 'lab-IT', 'description': 'Information Technology Lab'},
            {'name': 'lab-Chemistry', 'description': 'Chemistry Laboratory'},
            {'name': 'lab-Physics', 'description': 'Physics Laboratory'},
            {'name': 'lab-Biology', 'description': 'Biology Laboratory'},
            {'name': 'lab-OP', 'description': 'Optometry Practical Lab'},
        ]

        # Your exact Course Types (fixed typo in "Practical")
        course_types = [
            {'name': 'lecture', 'description': 'Theory-based instruction'},
            {'name': 'Practical', 'description': 'Hands-on training session'},
            {'name': 'Tutorial', 'description': 'Small-group problem solving'},
        ]

        # Load Room Types
        self.stdout.write(self.style.HTTP_INFO("=== LOADING ROOM TYPES ==="))
        for rt in room_types:
            obj, created = RoomType.objects.get_or_create(
                name=rt['name'],
                defaults={'description': rt['description']}
            )
            self.stdout.write(
                self.style.SUCCESS(f"✓ {rt['name']}") if created 
                else f"✓ {rt['name']} (already exists)"
            )

        # Load Lab Types (your exact data)
        self.stdout.write(self.style.HTTP_INFO("\n=== LOADING LAB TYPES ==="))
        for lt in lab_types:
            obj, created = LabType.objects.get_or_create(
                name=lt['name'],
                defaults={'description': lt['description']}
            )
            self.stdout.write(
                self.style.SUCCESS(f"✓ {lt['name']}") if created 
                else f"✓ {lt['name']} (already exists)"
            )

        # Load Course Types (your exact data)
        self.stdout.write(self.style.HTTP_INFO("\n=== LOADING COURSE TYPES ==="))
        for ct in course_types:
            obj, created = CourseType.objects.get_or_create(
                name=ct['name'],
                defaults={'description': ct['description']}
            )
            self.stdout.write(
                self.style.SUCCESS(f"✓ {ct['name']}") if created 
                else f"✓ {ct['name']} (already exists)"
            )

        self.stdout.write(
            self.style.SUCCESS("\n✔ COMPLETED! All types are now ready.")
        )