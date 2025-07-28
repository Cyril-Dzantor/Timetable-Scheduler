from django.core.management.base import BaseCommand
from Timetable.models import ClassStudent, CourseRegistration, Class, Course

class Command(BaseCommand):
    help = "Load student index numbers into ClassStudent and CourseRegistration"

    def handle(self, *args, **options):
        # ======= Input Data ========

        classes = [
            'CS100', 'CS200', 'CS300', 'CS400',
            'OP100', 'OP200', 'OP300', 'OP400', 'OP500', 'OP600',
            'BS100', 'BS200', 'BS300', 'BS400',
            'CHEM100', 'CHEM200', 'CHEM300', 'CHEM400',
            'IT100','IT200','IT300','IT400',
            'BIOCHEM100','BIOCHEM200','BIOCHEM300','BIOCHEM400',
            'PHYS100', 'PHYS200','PHYS300','PHYS400',
        ]
        class_size = {
            'CS100': 320, 'CS200': 220, 'CS300': 330, 'CS400': 250,
            'OP100': 100, 'OP200': 90, 'OP300': 85, 'OP400': 80, 'OP500': 75, 'OP600': 70,
            'BS100': 110, 'BS200': 100, 'BS300': 95, 'BS400': 90,
            'CHEM100': 105, 'CHEM200': 95, 'CHEM300': 90, 'CHEM400': 85,
            'IT100': 200,'IT200': 180,'IT300': 220,'IT400' : 150,
            'BIOCHEM100':135,'BIOCHEM200' : 150,'BIOCHEM300' : 165,'BIOCHEM400': 218,
            'PHYS100': 143, 'PHYS200':120,'PHYS300':120,'PHYS400': 130,
        }

        course_class_mapping = {
            # CS Courses
            'CS101': ['CS100', 'IT100', 'BIOCHEM100', 'CHEM100', 'PHYS100'],
            'CS102': ['CS100', 'BIOCHEM200', 'CHEM200', 'PHYS200'],
            'CS201': ['CS200', 'PHYS200', 'BIOCHEM300', 'IT200'],
            'CS202': ['CS200', 'BIOCHEM300', 'CHEM300'],
            'CS301': ['CS300', 'IT300'],
            'CS302': ['CS300'],
            'CS401': ['CS400', 'IT400'],
            'CS402': ['CS400'],

            # OP Courses
            'OP101': ['OP100'],
            'OP102': ['OP100'],
            'OP201': ['OP200'],
            'OP202': ['OP200'],
            'OP301': ['OP300'],
            'OP302': ['OP300'],
            'OP401': ['OP400'],
            'OP402': ['OP400'],
            'OP501': ['OP500'],
            'OP502': ['OP500'],
            'OP601': ['OP600'],
            'OP602': ['OP600'],

            # BS Courses
            'BS101': ['BS100'],
            'BS102': ['BS100'],
            'BS201': ['BS200'],
            'BS202': ['BS200'],
            'BS301': ['BS300'],
            'BS302': ['BS300'],
            'BS401': ['BS400'],
            'BS402': ['BS400'],

            # CHEM Courses
            'CHEM101': ['CHEM100'],
            'CHEM102': ['CHEM100'],
            'CHEM201': ['CHEM200'],
            'CHEM202': ['CHEM200'],
            'CHEM301': ['CHEM300'],
            'CHEM302': ['CHEM300'],
            'CHEM401': ['CHEM400'],
            'CHEM402': ['CHEM400'],

            # IT Courses
            'IT101': ['IT100', 'OP100', 'BS100'],
            'IT102': ['IT100', 'OP100', 'BS100', 'CS200'],
            'IT201': ['IT200', 'OP200', 'BS200'],
            'IT202': ['IT200'],
            'IT301': ['IT300', 'OP300', 'BS300'],
            'IT302': ['IT300', 'CS300'],
            'IT401': ['IT400', 'OP400', 'BS400'],
            'IT402': ['IT400', 'CS400'],

            # BIOCHEM Courses
            'BIOCHEM101': ['BIOCHEM100'],
            'BIOCHEM102': ['BIOCHEM100'],
            'BIOCHEM201': ['BIOCHEM200'],
            'BIOCHEM202': ['BIOCHEM200'],
            'BIOCHEM301': ['BIOCHEM300'],
            'BIOCHEM302': ['BIOCHEM300'],
            'BIOCHEM401': ['BIOCHEM400'],
            'BIOCHEM402': ['BIOCHEM400'],

            # PHYS Courses
            'PHYS101': ['PHYS100'],
            'PHYS102': ['PHYS100'],
            'PHYS201': ['PHYS200'],
            'PHYS202': ['PHYS200'],
            'PHYS301': ['PHYS300'],
            'PHYS302': ['PHYS300'],
            'PHYS401': ['PHYS400'],
            'PHYS402': ['PHYS400'],

            # General  Courses
            'Math101': ['CS100', 'OP100', 'BS100', 'CHEM100', 'IT100', 'BIOCHEM100', 'PHYS100'],
            'Stat150': ['CS200', 'IT200', 'OP200'],
            'Stat350': ['CS300', 'IT300'],
            'Psych150': ['CS100', 'OP100', 'BS100', 'IT100'],
            'History102': ['CS400', 'OP300', 'BS300'],
            'Econs205': ['BS200'],
            'Physics202': ['CHEM200', 'BIOCHEM200', 'PHYS200'],
            'Chem101': ['CHEM100', 'BIOCHEM100'],
            'Bio301': ['BIOCHEM300'],
            'Geo110': ['PHYS300']
        }

        # ======= Generate student index numbers per class ========
        student_index_numbers = {
            cls: [f"{cls}-{i:03d}" for i in range(1, class_size[cls]+1)]
            for cls in classes
        }

        # ======= Load into ClassStudent ========
        print("Loading ClassStudent data...")
        class_instances = {c.code: c for c in Class.objects.all()}
        added = 0
        for cls_code, index_list in student_index_numbers.items():
            cls_obj = class_instances.get(cls_code)
            if not cls_obj:
                self.stderr.write(f"Class not found: {cls_code}")
                continue
            for student_index in index_list:
                ClassStudent.objects.get_or_create(
                    assigned_class=cls_obj,
                    student_index=student_index
                )
                added += 1
        print(f"✅ Loaded {added} class student records")

        # ======= Load into CourseRegistration ========
        print("Loading CourseRegistration data...")
        course_instances = {c.code: c for c in Course.objects.all()}
        added = 0
        for course_code, class_list in course_class_mapping.items():
            course_obj = course_instances.get(course_code)
            if not course_obj:
                self.stderr.write(f"Course not found: {course_code}")
                continue
            for cls in class_list:
                students = student_index_numbers.get(cls, [])
                for student_index in students:
                    CourseRegistration.objects.get_or_create(
                        course=course_obj,
                        student_index=student_index
                    )
                    added += 1
        print(f"✅ Loaded {added} course registration records")
