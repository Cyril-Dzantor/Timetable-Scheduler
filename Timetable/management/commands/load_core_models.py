from django.core.management.base import BaseCommand
from Timetable.models import (
    Lecturer, Class, Room,
    Department, Building,
    RoomType, LabType
)
from datetime import datetime
import json

class Command(BaseCommand):
    help = 'Load core models (Lecturers, Classes, Rooms) with exact dataset'

    def handle(self, *args, **kwargs):
        self.load_classes()
        self.load_rooms()
        self.load_lecturers()
        self.stdout.write(self.style.SUCCESS("✔ Core models loaded successfully!"))

    def load_classes(self):
        self.stdout.write("\n=== LOADING CLASSES ===")
        
        classes_data = [
            {'code': 'CS100', 'dept': 'CS', 'level': 100, 'size': 320},
            {'code': 'CS200', 'dept': 'CS', 'level': 200, 'size': 220},
            {'code': 'CS300', 'dept': 'CS', 'level': 300, 'size': 330},
            {'code': 'CS400', 'dept': 'CS', 'level': 400, 'size': 250},
            {'code': 'OP100', 'dept': 'OP', 'level': 100, 'size': 100},
            {'code': 'OP200', 'dept': 'OP', 'level': 200, 'size': 90},
            {'code': 'OP300', 'dept': 'OP', 'level': 300, 'size': 85},
            {'code': 'OP400', 'dept': 'OP', 'level': 400, 'size': 80},
            {'code': 'OP500', 'dept': 'OP', 'level': 500, 'size': 75},
            {'code': 'OP600', 'dept': 'OP', 'level': 600, 'size': 70},
            {'code': 'BS100', 'dept': 'BS', 'level': 100, 'size': 110},
            {'code': 'BS200', 'dept': 'BS', 'level': 200, 'size': 100},
            {'code': 'BS300', 'dept': 'BS', 'level': 300, 'size': 95},
            {'code': 'BS400', 'dept': 'BS', 'level': 400, 'size': 90},
            {'code': 'CHEM100', 'dept': 'CHEM', 'level': 100, 'size': 105},
            {'code': 'CHEM200', 'dept': 'CHEM', 'level': 200, 'size': 95},
            {'code': 'CHEM300', 'dept': 'CHEM', 'level': 300, 'size': 90},
            {'code': 'CHEM400', 'dept': 'CHEM', 'level': 400, 'size': 85},
            {'code': 'IT100', 'dept': 'IT', 'level': 100, 'size': 200},
            {'code': 'IT200', 'dept': 'IT', 'level': 200, 'size': 180},
            {'code': 'IT300', 'dept': 'IT', 'level': 300, 'size': 220},
            {'code': 'IT400', 'dept': 'IT', 'level': 400, 'size': 150},
            {'code': 'BIOCHEM100', 'dept': 'BIOCHEM', 'level': 100, 'size': 135},
            {'code': 'BIOCHEM200', 'dept': 'BIOCHEM', 'level': 200, 'size': 150},
            {'code': 'BIOCHEM300', 'dept': 'BIOCHEM', 'level': 300, 'size': 165},
            {'code': 'BIOCHEM400', 'dept': 'BIOCHEM', 'level': 400, 'size': 218},
            {'code': 'PHYS100', 'dept': 'PHYS', 'level': 100, 'size': 143},
            {'code': 'PHYS200', 'dept': 'PHYS', 'level': 200, 'size': 120},
            {'code': 'PHYS300', 'dept': 'PHYS', 'level': 300, 'size': 120},
            {'code': 'PHYS400', 'dept': 'PHYS', 'level': 400, 'size': 130},
        ]

        for data in classes_data:
            try:
                dept = Department.objects.get(code=data['dept'])
                Class.objects.get_or_create(
                    code=data['code'],
                    defaults={
                        'name': f"{dept.name} Year {data['level']}",
                        'department': dept,
                        'level': data['level'],
                        'size': data['size']
                    }
                )
                self.stdout.write(f"✓ Class {data['code']} loaded")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Error loading {data['code']}: {str(e)}"))

    def load_rooms(self):
        self.stdout.write("\n=== LOADING ROOMS ===")

        rooms_data = [
        {'code': 'GF1', 'building': 'COSB', 'type': 'Lecture Hall', 'lab_type': None,
        'capacity': 400, 'dimensions': '40 x 10', 'max_courses': 3, 'proctors': 6, 'overflow': False},
        {'code': 'FF1', 'building': 'COSB', 'type': 'Lecture Hall', 'lab_type': None,
        'capacity': 400, 'dimensions': '40 x 10', 'max_courses': 3, 'proctors': 6, 'overflow': False},
        {'code': 'TF1', 'building': 'COSB', 'type': 'Lecture Hall', 'lab_type': None,
        'capacity': 400, 'dimensions': '40 x 10', 'max_courses': 3, 'proctors': 6, 'overflow': False},

        {'code': 'GF7', 'building': 'COSB', 'type': 'Classroom', 'lab_type': None,
        'capacity': 200, 'dimensions': '20 x 5', 'max_courses': 2, 'proctors': 2, 'overflow': False},
        {'code': 'GF8', 'building': 'COSB', 'type': 'Classroom', 'lab_type': None,
        'capacity': 200, 'dimensions': '20 x 5', 'max_courses': 2, 'proctors': 2, 'overflow': False},
        {'code': 'GF20', 'building': 'COSB', 'type': 'Classroom', 'lab_type': None,
        'capacity': 150, 'dimensions': '25 x 6', 'max_courses': 2, 'proctors': 3, 'overflow': False},

        {'code': 'FF7', 'building': 'COSB', 'type': 'Classroom', 'lab_type': None,
        'capacity': 200, 'dimensions': '20 x 5', 'max_courses': 2, 'proctors': 2, 'overflow': False},
        {'code': 'FF8', 'building': 'COSB', 'type': 'Classroom', 'lab_type': None,
        'capacity': 200, 'dimensions': '20 x 5', 'max_courses': 2, 'proctors': 2, 'overflow': False},
        {'code': 'FF20', 'building': 'COSB', 'type': 'Classroom', 'lab_type': None,
        'capacity': 150, 'dimensions': '25 x 6', 'max_courses': 2, 'proctors': 3, 'overflow': False},

        {'code': 'SF7', 'building': 'COSB', 'type': 'Classroom', 'lab_type': None,
        'capacity': 200, 'dimensions': '20 x 5', 'max_courses': 2, 'proctors': 2, 'overflow': False},
        {'code': 'SF8', 'building': 'COSB', 'type': 'Classroom', 'lab_type': None,
        'capacity': 200, 'dimensions': '20 x 5', 'max_courses': 2, 'proctors': 2, 'overflow': False},
        {'code': 'SF20', 'building': 'COSB', 'type': 'Classroom', 'lab_type': None,
        'capacity': 150, 'dimensions': '25 x 6', 'max_courses': 2, 'proctors': 3, 'overflow': False},

        {'code': 'TF7', 'building': 'COSB', 'type': 'Classroom', 'lab_type': None,
        'capacity': 200, 'dimensions': '20 x 5', 'max_courses': 2, 'proctors': 2, 'overflow': False},
        {'code': 'TF8', 'building': 'COSB', 'type': 'Classroom', 'lab_type': None,
        'capacity': 200, 'dimensions': '20 x 5', 'max_courses': 2, 'proctors': 2, 'overflow': False},
        {'code': 'TF20', 'building': 'COSB', 'type': 'Classroom', 'lab_type': None,
        'capacity': 150, 'dimensions': '25 x 6', 'max_courses': 2, 'proctors': 3, 'overflow': False},

        {'code': 'LectureHall-A', 'building': 'COSB', 'type': 'Lecture Hall', 'lab_type': None,
        'capacity': 301, 'dimensions': '43 x 7', 'max_courses': 3, 'proctors': 6, 'overflow': True},
        {'code': 'LectureHall-B', 'building': 'COSB', 'type': 'Lecture Hall', 'lab_type': None,
        'capacity': 301, 'dimensions': '43 x 7', 'max_courses': 3, 'proctors': 6, 'overflow': True},
        {'code': 'LectureHall-C', 'building': 'COSB', 'type': 'Lecture Hall', 'lab_type': None,
        'capacity': 252, 'dimensions': '36 x 7', 'max_courses': 3, 'proctors': 5, 'overflow': True},

        {'code': 'Lab-1', 'building': 'COSB', 'type': 'Laboratory', 'lab_type': 'lab-IT',
        'capacity': 150, 'dimensions': '75 x 2', 'max_courses': 1, 'proctors': 2, 'overflow': False},
        {'code': 'Lab-2', 'building': 'COSB', 'type': 'Laboratory', 'lab_type': 'lab-Chemistry',
        'capacity': 150, 'dimensions': '75 x 2', 'max_courses': 1, 'proctors': 2, 'overflow': False},
        {'code': 'Lab-3', 'building': 'COSB', 'type': 'Laboratory', 'lab_type': 'lab-Physics',
        'capacity': 150, 'dimensions': '75 x 2', 'max_courses': 1, 'proctors': 2, 'overflow': False},
        {'code': 'Lab-4', 'building': 'COSB', 'type': 'Laboratory', 'lab_type': 'lab-Biology',
        'capacity': 150, 'dimensions': '75 x 2', 'max_courses': 1, 'proctors': 2, 'overflow': False},
        {'code': 'Lab-5', 'building': 'COSB', 'type': 'Laboratory', 'lab_type': 'lab-OP',
        'capacity': 150, 'dimensions': '75 x 2', 'max_courses': 1, 'proctors': 2, 'overflow': False},
        {'code': 'Lab-6', 'building': 'COSB', 'type': 'Laboratory', 'lab_type': 'lab-IT',
        'capacity': 150, 'dimensions': '75 x 2', 'max_courses': 1, 'proctors': 2, 'overflow': False},
        {'code': 'Lab-8', 'building': 'COSB', 'type': 'Laboratory', 'lab_type': 'lab-Physics',
        'capacity': 150, 'dimensions': '75 x 2', 'max_courses': 1, 'proctors': 2, 'overflow': False},
        {'code': 'Lab-9', 'building': 'COSB', 'type': 'Laboratory', 'lab_type': 'lab-Biology',
        'capacity': 150, 'dimensions': '75 x 2', 'max_courses': 1, 'proctors': 2, 'overflow': False},
        {'code': 'Lab-10', 'building': 'COSB', 'type': 'Laboratory', 'lab_type': 'lab-OP',
        'capacity': 150, 'dimensions': '75 x 2', 'max_courses': 1, 'proctors': 2, 'overflow': False},
        {'code': 'Lab-11', 'building': 'COSB', 'type': 'Laboratory', 'lab_type': 'lab-IT',
        'capacity': 150, 'dimensions': '75 x 2', 'max_courses': 1, 'proctors': 2, 'overflow': False},
        {'code': 'Lab-12', 'building': 'COSB', 'type': 'Laboratory', 'lab_type': 'lab-Chemistry',
        'capacity': 150, 'dimensions': '75 x 2', 'max_courses': 1, 'proctors': 2, 'overflow': False},
        {'code': 'Lab-13', 'building': 'COSB', 'type': 'Laboratory', 'lab_type': 'lab-Physics',
        'capacity': 150, 'dimensions': '75 x 2', 'max_courses': 1, 'proctors': 2, 'overflow': False},
        {'code': 'Lab-14', 'building': 'COSB', 'type': 'Laboratory', 'lab_type': 'lab-Biology',
        'capacity': 150, 'dimensions': '75 x 2', 'max_courses': 1, 'proctors': 2, 'overflow': False},
        {'code': 'Lab-15', 'building': 'COSB', 'type': 'Laboratory', 'lab_type': 'lab-OP',
        'capacity': 150, 'dimensions': '75 x 2', 'max_courses': 1, 'proctors': 2, 'overflow': False},

        {'code': 'Room-101', 'building': 'COSB', 'type': 'Classroom', 'lab_type': None,
        'capacity': 150, 'dimensions': '30 x 5', 'max_courses': 2, 'proctors': 3, 'overflow': False},
        {'code': 'Room-102', 'building': 'COSB', 'type': 'Classroom', 'lab_type': None,
        'capacity': 150, 'dimensions': '30 x 5', 'max_courses': 2, 'proctors': 3, 'overflow': False},
        {'code': 'Room-103', 'building': 'COSB', 'type': 'Classroom', 'lab_type': None,
        'capacity': 100, 'dimensions': '25 x 4', 'max_courses': 2, 'proctors': 2, 'overflow': False}
     ]


        for data in rooms_data:
            try:
                building = Building.objects.get(code=data['building'])
                room_type = RoomType.objects.get(name=data['type'])
                lab_type = LabType.objects.get(name=data['lab_type']) if data['lab_type'] else None

                Room.objects.get_or_create(
                    code=data['code'],
                    defaults={
                        'building': building,
                        'room_type': room_type,
                        'lab_type': lab_type,
                        'capacity': data['capacity'],
                        'dimensions': data['dimensions'],
                        'max_courses': data['max_courses'],
                        'proctors_required': data['proctors'],
                        'is_overflow': data['overflow']
                    }
                )
                self.stdout.write(f"✓ Room {data['code']} loaded")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Error loading {data['code']}: {str(e)}"))

    def load_lecturers(self):
        self.stdout.write("\n=== LOADING LECTURERS ===")
        
        lecturers_data = [
            {
                'name': 'Dr. Smith',
                'dept': 'CS',
                'courses': ['CS101', 'CS301', 'IT102'],
                'is_proctor': True,
                'availability': {
                    'Monday': ['8:00 - 8:55', '9:00 - 9:55'], 
                    'Tuesday': ['8:00 - 8:55', '9:00 - 9:55', '17:00 - 17:55', '18:00 - 18:55'],
                    'Thursday': ['8:00 - 8:55', '9:00 - 9:55', '13:00 - 13:55', '14:00 - 14:55']
                }
            },
            {
                'name': 'Dr. Johnson',
                'dept': 'CS',
                'courses': ['Math101', 'IT201'],
                'is_proctor': True,
                'availability': {
                    'Tuesday': ['8:00 - 8:55', '9:00 - 9:55', '16:00 - 16:55', '17:00 - 17:55'],
                    'Wednesday': ['10:30 - 11:25', '11:30 - 12:25'], 
                    'Thursday': ['11:30 - 12:25', '13:00 - 13:55'],
                    'Monday': ['16:00 - 16:55', '17:00 - 17:55']
                }
            },
            {
                'name': 'Prof. Williams',
                'dept': 'OP',
                'courses': ['OP101', 'OP102', 'OP501'],
                'is_proctor': False,
                'availability': {}
            },
            {
                'name': 'Dr. Brown',
                'dept': 'OP',
                'courses': ['OP201', 'OP202', 'OP601'],
                'is_proctor': False,
                'availability': {}
            },
            {
                'name': 'Dr. Jones',
                'dept': 'BS',
                'courses': ['BIOCHEM201', 'BIOCHEM202', 'BS101', 'BS102'],
                'is_proctor': False,
                'availability': {}
            },
            {
                'name': 'Dr. Miller',
                'dept': 'BS',
                'courses': ['BIOCHEM301', 'BIOCHEM302', 'BS201', 'BS202'],
                'is_proctor': True,
                'availability': {}
            },
            {
                'name': 'Prof. Davis',
                'dept': 'CHEM',
                'courses': ['CHEM201', 'CHEM202'],
                'is_proctor': True,
                'availability': {}
            },
            {
                'name': 'Dr. Wilson',
                'dept': 'CHEM',
                'courses': ['CHEM401', 'CHEM402'],
                'is_proctor': False,
                'availability': {}
            },
            {
                'name': 'Dr. Anderson',
                'dept': 'CS',
                'courses': ['CS101', 'CS201', 'IT101'],
                'is_proctor': True,
                'availability': {}
            },
            {
                'name': 'Dr. Thomas',
                'dept': 'OP',
                'courses': ['OP401', 'OP402', 'OP602'],
                'is_proctor': True,
                'availability': {}
            },
            {
                'name': 'Prof. White',
                'dept': 'CS',
                'courses': ['BIOCHEM401', 'BIOCHEM402', 'BS301', 'BS302', 'BS401', 'BS402'],
                'is_proctor': True,
                'availability': {}
            },
            {
                'name': 'Dr. Taylor',
                'dept': 'CHEM',
                'courses': ['CHEM102'],
                'is_proctor': True,
                'availability': {}
            },
            {
                'name': 'Dr. Moore',
                'dept': 'OP',
                'courses': ['OP301', 'OP302', 'OP502'],
                'is_proctor': True,
                'availability': {}
            },
            {
                'name': 'Dr. Jackson',
                'dept': 'CS',
                'courses': ['CS101', 'CS201', 'IT302', 'CS401'],
                'is_proctor': True,
                'availability': {}
            },
            {
                'name': 'Dr. Martin',
                'dept': 'CHEM',
                'courses': ['CHEM301'],
                'is_proctor': False,
                'availability': {}
            },
            {
                'name': 'Dr. Humboldt',
                'dept': 'GEOG',
                'courses': ['Geo110'],
                'is_proctor': False,
                'availability': {}
            },
            {
                'name': 'Dr. Euler',
                'dept': 'MATSTAT',
                'courses': ['Math101', 'Stat350'],
                'is_proctor': True,
                'availability': {
                    'Monday': ['8:00 - 8:55', '9:00 - 9:55'],
                    'Tuesday': ['10:00 - 10:55', '11:00 - 11:55'],
                    'Wednesday': ['14:00 - 14:55', '15:00 - 15:55'],
                    'Thursday': ['16:00 - 16:55', '17:00 - 17:55'],
                    'Friday': ['9:00 - 9:55', '10:00 - 10:55']
                }
            },
            {
                'name': 'Dr. Newton',
                'dept': 'PHYS',
                'courses': ['Physics202', 'PHYS101', 'PHYS201'],
                'is_proctor': True,
                'availability': {
                    'Monday': ['8:00 - 8:55', '9:00 - 9:55'],
                    'Tuesday': ['10:30 - 11:25', '11:30 - 12:25'],
                    'Wednesday': ['14:00 - 14:55', '15:00 - 15:55'],
                    'Thursday': ['13:00 - 13:55', '14:00 - 14:55'],
                    'Friday': ['10:00 - 10:55', '11:00 - 11:55']
                }
            },
            {
                'name': 'Dr. Curie',
                'dept': 'CHEM',
                'courses': ['Chem101', 'CHEM101'],
                'is_proctor': True,
                'availability': {
                    'Monday': ['10:00 - 10:55', '11:00 - 11:55'],
                    'Tuesday': ['14:00 - 14:55', '15:00 - 15:55'],
                    'Wednesday': ['14:00 - 14:55', '15:00 - 15:55'],
                    'Thursday': ['10:00 - 10:55', '11:00 - 11:55'],
                    'Friday': ['15:00 - 15:55', '16:00 - 16:55']
                }
            },
            {
                'name': 'Dr. Mendeleev',
                'dept': 'CHEM',
                'courses': ['CHEM302'],
                'is_proctor': False,
                'availability': {}
            },
            {
                'name': 'Dr. Darwin',
                'dept': 'BS',
                'courses': ['BIOCHEM101', 'BIOCHEM102', 'Bio301'],
                'is_proctor': True,
                'availability': {
                    'Monday': ['16:00 - 16:55', '17:00 - 17:55'],
                    'Tuesday': ['17:00 - 17:55', '18:00 - 18:55'],
                    'Wednesday': ['10:00 - 10:55', '11:00 - 11:55'],
                    'Thursday': ['14:00 - 14:55', '15:00 - 15:55'],
                    'Friday': ['12:00 - 12:55', '13:00 - 13:55']
                }
            },
            {
                'name': 'Dr. Turing',
                'dept': 'CS',
                'courses': ['CS102', 'CS302', 'IT301', 'IT401'],
                'is_proctor': True,
                'availability': {}
            },
            {
                'name': 'Dr. Lovelace',
                'dept': 'CS',
                'courses': ['CS102', 'CS301', 'CS402', 'IT202', 'IT402'],
                'is_proctor': False,
                'availability': {}
            },
            {
                'name': 'Dr. Herodotus',
                'dept': 'HISTPOL',
                'courses': ['History102'],
                'is_proctor': False,
                'availability': {}
            },
            {
                'name': 'Dr. Keynes',
                'dept': 'ECONS',
                'courses': ['Econs205'],
                'is_proctor': False,
                'availability': {}
            },
            {
                'name': 'Dr. Freud',
                'dept': 'PSYCH',
                'courses': ['Psych150'],
                'is_proctor': False,
                'availability': {}
            },
            {
                'name': 'Dr. Jung',
                'dept': 'PSYCH',
                'courses': ['Psych150'],
                'is_proctor': False,
                'availability': {}
            },
            {
                'name': 'Dr. Bayes',
                'dept': 'MATSTAT',
                'courses': ['Math101', 'Stat150'],
                'is_proctor': True,
                'availability': {}
            }
        ]


        for data in lecturers_data:
            try:
                dept = Department.objects.get(code=data['dept'])
                lecturer, created = Lecturer.objects.get_or_create(
                    name=data['name'],
                    department=dept,
                    defaults={
                        'is_proctor': data['is_proctor'],
                        'availability': data['availability'],
                        'max_courses': 4,
                        'is_active': True
                    }
                )
                self.stdout.write(f"✓ Lecturer {data['name']} loaded")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Error loading {data['name']}: {str(e)}"))