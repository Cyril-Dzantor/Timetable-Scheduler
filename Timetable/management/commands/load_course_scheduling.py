from django.core.management.base import BaseCommand
from Timetable.models import (
    Course, CourseType, Department,
    Lecturer, Class, LabType,
    TimeSlot, ExamDate, ProctorAssignment
)
from datetime import datetime, time
import json

class Command(BaseCommand):
    help = 'Load courses, time slots, exam dates and proctor assignments'

    def handle(self, *args, **kwargs):
        self.load_time_slots()
        self.load_exam_dates()
        self.load_courses()
        self.load_proctor_assignments()
        self.stdout.write(self.style.SUCCESS("✔ Scheduling data loaded successfully!"))

    def load_time_slots(self):
        self.stdout.write("\n=== LOADING TIME SLOTS ===")
        
        # Lecture slots
        lecture_slots = [
            ('8:00', '8:55'), ('9:00', '9:55'), 
            ('10:30', '11:25'), ('11:30', '12:25'),
            ('13:00', '13:55'), ('14:00', '14:55'),
            ('15:00', '15:55'), ('16:00', '16:55'),
            ('17:00', '17:55'), ('18:00', '18:55')
        ]

        

        # Exam slots
        exam_slots = [
            ('8:30', '10:30'), ('12:00', '14:00'), ('15:00', '17:00')
        ]

        for start, end in lecture_slots:
            start_time = time(*map(int, start.split(':')))
            end_time = time(*map(int, end.split(':')))
            code = f"LEC_{start.replace(':', '')}_{end.replace(':', '')}"
            
            TimeSlot.objects.get_or_create(
                start_time=start_time,
                end_time=end_time,
                defaults={
                    'code': code,
                    'is_lecture_slot': True,
                    'is_exam_slot': False
                }
            )
            self.stdout.write(f"✓ Lecture slot {start}-{end} loaded")

        for start, end in exam_slots:
            start_time = time(*map(int, start.split(':')))
            end_time = time(*map(int, end.split(':')))
            code = f"EXAM_{start.replace(':', '')}_{end.replace(':', '')}"
            
            TimeSlot.objects.get_or_create(
                start_time=start_time,
                end_time=end_time,
                defaults={
                    'code': code,
                    'is_lecture_slot': False,
                    'is_exam_slot': True
                }
            )
            self.stdout.write(f"✓ Exam slot {start}-{end} loaded")

    def load_exam_dates(self):
        self.stdout.write("\n=== LOADING EXAM DATES ===")
        
        exam_dates = [
            '2025-05-01', '2025-05-02', '2025-05-03', '2025-05-04',
            '2025-05-05', '2025-05-06', '2025-05-07', '2025-05-08',
            '2025-05-09', '2025-05-10', '2025-05-11', '2025-05-12'
        ]

        for date_str in exam_dates:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            day_name = date.strftime('%A')
            
            ExamDate.objects.get_or_create(
                date=date,
                defaults={'day_name': day_name}
            )
            self.stdout.write(f"✓ Exam date {date_str} ({day_name}) loaded")

    def load_courses(self):
        self.stdout.write("\n=== LOADING COURSES ===")
        
        courses_data = {
    # CS Courses
    'CS101': {
        'title': 'Introduction to Computer Science',
        'type': 'lecture',
        'dept': 'CS',
        'credit_hours': 2,
        'enrollment': 903,
        'classes': ['CS100', 'IT100', 'BIOCHEM100', 'CHEM100', 'PHYS100'],
        'lecturers': ['Dr. Smith', 'Dr. Jackson', 'Dr. Anderson'],
        'requires_lab': True,
        'lab_type': 'lab-IT'
    },
    'CS102': {
        'title': 'Data Structures',
        'type': 'lecture',
        'dept': 'CS',
        'credit_hours': 3,
        'enrollment': 685,
        'classes': ['CS100', 'BIOCHEM200', 'CHEM200', 'PHYS200'],
        'lecturers': ['Dr. Lovelace', 'Dr. Turing'],
        'requires_lab': False
    },
    'CS201': {
        'title': 'Algorithms',
        'type': 'lecture',
        'dept': 'CS',
        'credit_hours': 3,
        'enrollment': 685,
        'classes': ['CS200', 'PHYS200', 'BIOCHEM300', 'IT200'],
        'lecturers': ['Dr. Anderson', 'Dr. Jackson'],
        'requires_lab': False
    },
    'CS202': {
        'title': 'Computer Architecture',
        'type': 'lecture',
        'dept': 'CS',
        'credit_hours': 2,
        'enrollment': 475,
        'classes': ['CS200', 'BIOCHEM300', 'CHEM300'],
        'lecturers': ['Dr. Smith','Dr. Anderson'],
        'requires_lab': False,
    },
    'CS301': {
        'title': 'Operating Systems',
        'type': 'lecture',
        'dept': 'CS',
        'credit_hours': 2,
        'enrollment': 550,
        'classes': ['CS300', 'IT300'],
        'lecturers': ['Dr. Smith', 'Dr. Lovelace'],
        'requires_lab': False,
    },
    'CS302': {
        'title': 'Database Systems',
        'type': 'lecture',
        'dept': 'CS',
        'credit_hours': 3,
        'enrollment': 330,
        'classes': ['CS300'],
        'lecturers': ['Dr. Turing'],
        'requires_lab': True,
        'lab_type': 'lab-IT'
    },
    'CS401': {
        'title': 'Artificial Intelligence',
        'type': 'lecture',
        'dept': 'CS',
        'credit_hours': 2,
        'enrollment': 400,
        'classes': ['CS400', 'IT400'],
        'lecturers': ['Dr. Jackson'],
        'requires_lab': False
    },
    'CS402': {
        'title': 'Machine Learning',
        'type': 'lecture',
        'dept': 'CS',
        'credit_hours': 3,
        'enrollment': 250,
        'classes': ['CS400'],
        'lecturers': ['Dr. Lovelace'],
        'requires_lab': False
    },

    # OP Courses
    'OP101': {
        'title': 'Introduction to Optometry',
        'type': 'lecture',
        'dept': 'OP',
        'credit_hours': 3,
        'enrollment': 100,
        'classes': ['OP100'],
        'lecturers': ['Prof. Williams'],
        'requires_lab': True,
        'lab_type': 'lab-OP'
    },
    'OP102': {
        'title': 'Visual Optics',
        'type': 'lecture',
        'dept': 'OP',
        'credit_hours': 2,
        'enrollment': 100,
        'classes': ['OP100'],
        'lecturers': ['Prof. Williams'],
        'requires_lab': False,
        
    },
    'OP201': {
        'title': 'Ocular Anatomy',
        'type': 'lecture',
        'dept': 'OP',
        'credit_hours': 2,
        'enrollment': 90,
        'classes': ['OP200'],
        'lecturers': ['Dr. Brown'],
        'requires_lab': False,
    },
    'OP202': {
        'title': 'Clinical Optometry I',
        'type': 'lecture',
        'dept': 'OP',
        'credit_hours': 3,
        'enrollment': 90,
        'classes': ['OP200'],
        'lecturers': ['Dr. Brown'],
        'requires_lab': True,
        'lab_type': 'lab-OP'
    },
    'OP301': {
        'title': 'Binocular Vision',
        'type': 'lecture',
        'dept': 'OP',
        'credit_hours': 4,
        'enrollment': 85,
        'classes': ['OP300'],
        'lecturers': ['Dr. Moore'],
        'requires_lab': True,
        'lab_type': 'lab-OP'
    },
    'OP302': {
        'title': 'Contact Lens Studies',
        'type': 'lecture',
        'dept': 'OP',
        'credit_hours': 3,
        'enrollment': 85,
        'classes': ['OP300'],
        'lecturers': ['Dr. Moore'],
        'requires_lab': True,
        'lab_type': 'lab-OP'
    },
    'OP401': {
        'title': 'Low Vision',
        'type': 'lecture',
        'dept': 'OP',
        'credit_hours': 2,
        'enrollment': 80,
        'classes': ['OP400'],
        'lecturers': ['Dr. Thomas'],
        'requires_lab': False
    },
    'OP402': {
        'title': 'Clinical Optometry II',
        'type': 'lecture',
        'dept': 'OP',
        'credit_hours': 3,
        'enrollment': 80,
        'classes': ['OP400'],
        'lecturers': ['Dr. Thomas'],
        'requires_lab': True,
        'lab_type': 'lab-OP'
    },
    'OP501': {
        'title': 'Pediatric Optometry',
        'type': 'lecture',
        'dept': 'OP',
        'credit_hours': 4,
        'enrollment': 75,
        'classes': ['OP500'],
        'lecturers': ['Prof. Williams'],
        'requires_lab': False
    },
    'OP502': {
        'title': 'Geriatric Optometry',
        'type': 'lecture',
        'dept': 'OP',
        'credit_hours': 2,
        'enrollment': 75,
        'classes': ['OP500'],
        'lecturers': ['Dr. Moore'],
        'requires_lab': False
    },
    'OP601': {
        'title': 'Advanced Clinical Practice',
        'type': 'lecture',
        'dept': 'OP',
        'credit_hours': 3,
        'enrollment': 70,
        'classes': ['OP600'],
        'lecturers': ['Dr. Brown'],
        'requires_lab': True,
        'lab_type': 'lab-OP'
    },
    'OP602': {
        'title': 'Research in Optometry',
        'type': 'lecture',
        'dept': 'OP',
        'credit_hours': 4,
        'enrollment': 70,
        'classes': ['OP600'],
        'lecturers': ['Dr. Thomas'],
        'requires_lab': False
    },

    # BS Courses
    'BS101': {
        'title': 'Introduction to Biological Sciences',
        'type': 'lecture',
        'dept': 'BS',
        'credit_hours': 2,
        'enrollment': 110,
        'classes': ['BS100'],
        'lecturers': ['Dr. Jones'],
        'requires_lab': False,
    },
    'BS102': {
        'title': 'Cell Biology',
        'type': 'lecture',
        'dept': 'BS',
        'credit_hours': 3,
        'enrollment': 110,
        'classes': ['BS100'],
        'lecturers': ['Dr. Jones'],
        'requires_lab': True,
        'lab_type': 'lab-Biology'
    },
    'BS201': {
        'title': 'Genetics',
        'type': 'lecture',
        'dept': 'BS',
        'credit_hours': 3,
        'enrollment': 100,
        'classes': ['BS200'],
        'lecturers': ['Dr. Miller'],
        'requires_lab': True,
        'lab_type': 'lab-Biology'
    },
    'BS202': {
        'title': 'Microbiology',
        'type': 'lecture',
        'dept': 'BS',
        'credit_hours': 2,
        'enrollment': 100,
        'classes': ['BS200'],
        'lecturers': ['Dr. Miller'],
        'requires_lab': False,
    },
    'BS301': {
        'title': 'Biochemistry',
        'type': 'lecture',
        'dept': 'BS',
        'credit_hours': 3,
        'enrollment': 95,
        'classes': ['BS300'],
        'lecturers': ['Prof. White'],
        'requires_lab': False,
    },
    'BS302': {
        'title': 'Ecology',
        'type': 'lecture',
        'dept': 'BS',
        'credit_hours': 2,
        'enrollment': 95,
        'classes': ['BS300'],
        'lecturers': ['Prof. White'],
        'requires_lab': False,
    },
    'BS401': {
        'title': 'Evolutionary Biology',
        'type': 'lecture',
        'dept': 'BS',
        'credit_hours': 3,
        'enrollment': 90,
        'classes': ['BS400'],
        'lecturers': ['Prof. White'],
        'requires_lab': False
    },
    'BS402': {
        'title': 'Research Methods in Biology',
        'type': 'lecture',
        'dept': 'BS',
        'credit_hours': 2,
        'enrollment': 90,
        'classes': ['BS400'],
        'lecturers': ['Prof. White'],
        'requires_lab': False
    },

    # CHEM Courses
    'CHEM101': {
        'title': 'General Chemistry I',
        'type': 'lecture',
        'dept': 'CHEM',
        'credit_hours': 2,
        'enrollment': 105,
        'classes': ['CHEM100'],
        'lecturers': ['Dr. Curie'],
        'requires_lab': False
    },
    'CHEM102': {
        'title': 'General Chemistry II',
        'type': 'lecture',
        'dept': 'CHEM',
        'credit_hours': 3,
        'enrollment': 105,
        'classes': ['CHEM100'],
        'lecturers': ['Dr. Taylor'],
        'requires_lab': True,
        'lab_type': 'lab-Chemistry'
    },
    'CHEM201': {
        'title': 'Organic Chemistry I',
        'type': 'lecture',
        'dept': 'CHEM',
        'credit_hours': 3,
        'enrollment': 95,
        'classes': ['CHEM200'],
        'lecturers': ['Prof. Davis'],
        'requires_lab': True,
        'lab_type': 'lab-Chemistry'
    },
    'CHEM202': {
        'title': 'Organic Chemistry II',
        'type': 'lecture',
        'dept': 'CHEM',
        'credit_hours': 2,
        'enrollment': 95,
        'classes': ['CHEM200'],
        'lecturers': ['Prof. Davis'],
        'requires_lab': False,
    },
    'CHEM301': {
        'title': 'Physical Chemistry',
        'type': 'lecture',
        'dept': 'CHEM',
        'credit_hours': 2,
        'enrollment': 90,
        'classes': ['CHEM300'],
        'lecturers': ['Dr. Martin'],
        'requires_lab': False,
    },
    'CHEM302': {
        'title': 'Inorganic Chemistry',
        'type': 'lecture',
        'dept': 'CHEM',
        'credit_hours': 3,
        'enrollment': 90,
        'classes': ['CHEM300'],
        'lecturers': ['Dr. Mendeleev'],
        'requires_lab': True,
        'lab_type': 'lab-Chemistry'
    },
    'CHEM401': {
        'title': 'Analytical Chemistry',
        'type': 'lecture',
        'dept': 'CHEM',
        'credit_hours': 3,
        'enrollment': 85,
        'classes': ['CHEM400'],
        'lecturers': ['Dr. Wilson'],
        'requires_lab': True,
        'lab_type': 'lab-Chemistry'
    },
    'CHEM402': {
        'title': 'Advanced Topics in Chemistry',
        'type': 'lecture',
        'dept': 'CHEM',
        'credit_hours': 3,
        'enrollment': 85,
        'classes': ['CHEM400'],
        'lecturers': ['Dr. Wilson'],
        'requires_lab': False
    },

    # IT Courses
    'IT101': {
        'title': 'IT Fundamentals',
        'type': 'lecture',
        'dept': 'IT',
        'credit_hours': 2,
        'enrollment': 410,
        'classes': ['IT100', 'OP100', 'BS100'],
        'lecturers': ['Dr. Anderson'],
        'requires_lab': False,
    },
    'IT102': {
        'title': 'Web Development',
        'type': 'lecture',
        'dept': 'IT',
        'credit_hours': 3,
        'enrollment': 630,
        'classes': ['IT100', 'OP100', 'BS100', 'CS200'],
        'lecturers': ['Dr. Smith'],
        'requires_lab': True,
        'lab_type': 'lab-IT'
    },
    'IT201': {
        'title': 'Networking',
        'type': 'lecture',
        'dept': 'IT',
        'credit_hours': 3,
        'enrollment': 370,
        'classes': ['IT200', 'OP200', 'BS200'],
        'lecturers': ['Dr. Johnson'],
        'requires_lab': True,
        'lab_type': 'lab-IT'
    },
    'IT202': {
        'title': 'Database Systems',
        'type': 'lecture',
        'dept': 'IT',
        'credit_hours': 2,
        'enrollment': 180,
        'classes': ['IT200'],
        'lecturers': ['Dr. Lovelace'],
        'requires_lab': False,
    },
    'IT301': {
        'title': 'Systems Analysis',
        'type': 'lecture',
        'dept': 'IT',
        'credit_hours': 3,
        'enrollment': 400,
        'classes': ['IT300', 'OP300', 'BS300'],
        'lecturers': ['Dr. Turing'],
        'requires_lab': False
    },
    'IT302': {
        'title': 'Information Security',
        'type': 'lecture',
        'dept': 'IT',
        'credit_hours': 2,
        'enrollment': 550,
        'classes': ['IT300', 'CS300'],
        'lecturers': ['Dr. Jackson'],
        'requires_lab': False
    },
    'IT401': {
        'title': 'IT Project Management',
        'type': 'lecture',
        'dept': 'IT',
        'credit_hours': 3,
        'enrollment': 320,
        'classes': ['IT400', 'OP400', 'BS400'],
        'lecturers': ['Dr. Turing'],
        'requires_lab': False
    },
    'IT402': {
        'title': 'Emerging Technologies',
        'type': 'lecture',
        'dept': 'IT',
        'credit_hours': 2,
        'enrollment': 400,
        'classes': ['IT400', 'CS400'],
        'lecturers': ['Dr. Lovelace'],
        'requires_lab': False
    },

    # BIOCHEM Courses
    'BIOCHEM101': {
        'title': 'Introduction to Biochemistry',
        'type': 'lecture',
        'dept': 'BIOCHEM',
        'credit_hours': 2,
        'enrollment': 135,
        'classes': ['BIOCHEM100'],
        'lecturers': ['Dr. Darwin'],
        'requires_lab': False,
    },
    'BIOCHEM102': {
        'title': 'Metabolic Biochemistry',
        'type': 'lecture',
        'dept': 'BIOCHEM',
        'credit_hours': 3,
        'enrollment': 135,
        'classes': ['BIOCHEM100'],
        'lecturers': ['Dr. Darwin'],
        'requires_lab': True,
        'lab_type': 'lab-Biology'
    },
    'BIOCHEM201': {
        'title': 'Molecular Biology',
        'type': 'lecture',
        'dept': 'BIOCHEM',
        'credit_hours': 3,
        'enrollment': 150,
        'classes': ['BIOCHEM200'],
        'lecturers': ['Dr. Jones'],
        'requires_lab': True,
        'lab_type': 'lab-Biology'
    },
    'BIOCHEM202': {
        'title': 'Enzymology',
        'type': 'lecture',
        'dept': 'BIOCHEM',
        'credit_hours': 2,
        'enrollment': 150,
        'classes': ['BIOCHEM200'],
        'lecturers': ['Dr. Jones'],
        'requires_lab': False,
    },
    'BIOCHEM301': {
        'title': 'Medical Biochemistry',
        'type': 'lecture',
        'dept': 'BIOCHEM',
        'credit_hours': 3,
        'enrollment': 165,
        'classes': ['BIOCHEM300'],
        'lecturers': ['Dr. Miller'],
        'requires_lab': True,
        'lab_type': 'lab-Biology'
    },
    'BIOCHEM302': {
        'title': 'Immunology',
        'type': 'lecture',
        'dept': 'BIOCHEM',
        'credit_hours': 2,
        'enrollment': 165,
        'classes': ['BIOCHEM300'],
        'lecturers': ['Dr. Miller'],
        'requires_lab': False,
    },
    'BIOCHEM401': {
        'title': 'Research in Biochemistry',
        'type': 'lecture',
        'dept': 'BIOCHEM',
        'credit_hours': 3,
        'enrollment': 218,
        'classes': ['BIOCHEM400'],
        'lecturers': ['Prof. White'],
        'requires_lab': True,
        'lab_type': 'lab-Biology'
    },
    'BIOCHEM402': {
        'title': 'Advanced Biochemistry',
        'type': 'lecture',
        'dept': 'BIOCHEM',
        'credit_hours': 3,
        'enrollment': 218,
        'classes': ['BIOCHEM400'],
        'lecturers': ['Prof. White'],
        'requires_lab': False
    },

    # PHYS Courses
    'PHYS101': {
        'title': 'General Physics I',
        'type': 'lecture',
        'dept': 'PHYS',
        'credit_hours': 2,
        'enrollment': 143,
        'classes': ['PHYS100'],
        'lecturers': ['Dr. Newton'],
        'requires_lab': False,
    },
    'PHYS102': {
        'title': 'General Physics II',
        'type': 'lecture',
        'dept': 'PHYS',
        'credit_hours': 3,
        'enrollment': 143,
        'classes': ['PHYS100'],
        'lecturers': ['Dr. Newton'],
        'requires_lab': True,
        'lab_type': 'lab-Physics'
    },
    'PHYS201': {
        'title': 'Classical Mechanics',
        'type': 'lecture',
        'dept': 'PHYS',
        'credit_hours': 3,
        'enrollment': 120,
        'classes': ['PHYS200'],
        'lecturers': ['Dr. Newton'],
        'requires_lab': True,
        'lab_type': 'lab-Physics'
    },
    'PHYS202': {
        'title': 'Electromagnetism',
        'type': 'lecture',
        'dept': 'PHYS',
        'credit_hours': 2,
        'enrollment': 120,
        'classes': ['PHYS200'],
        'lecturers': ['Dr. Newton'],
        'requires_lab': False,
    },
    'PHYS301': {
        'title': 'Quantum Mechanics',
        'type': 'lecture',
        'dept': 'PHYS',
        'credit_hours': 2,
        'enrollment': 120,
        'classes': ['PHYS300'],
        'lecturers': ['Dr. Newton'],
        'requires_lab': False
    },
    'PHYS302': {
        'title': 'Thermodynamics',
        'type': 'lecture',
        'dept': 'PHYS',
        'credit_hours': 3,
        'enrollment': 120,
        'classes': ['PHYS300'],
        'lecturers': ['Dr. Newton'],
        'requires_lab': False
    },
    'PHYS401': {
        'title': 'Astrophysics',
        'type': 'lecture',
        'dept': 'PHYS',
        'credit_hours': 3,
        'enrollment': 130,
        'classes': ['PHYS400'],
        'lecturers': ['Dr. Newton'],
        'requires_lab': False
    },
    'PHYS402': {
        'title': 'Nuclear Physics',
        'type': 'lecture',
        'dept': 'PHYS',
        'credit_hours': 2,
        'enrollment': 130,
        'classes': ['PHYS400'],
        'lecturers': ['Dr. Newton'],
        'requires_lab': False
    },

    # General Courses
    'Math101': {
        'title': 'Calculus I',
        'type': 'lecture',
        'dept': 'MATSTAT',
        'credit_hours': 3,
        'enrollment': 1113,
        'classes': ['CS100', 'OP100', 'BS100', 'CHEM100', 'IT100', 'BIOCHEM100', 'PHYS100'],
        'lecturers': ['Dr. Euler', 'Dr. Bayes', 'Dr. Johnson'],
        'requires_lab': False
    },
    'Stat150': {
        'title': 'Introduction to Statistics',
        'type': 'lecture',
        'dept': 'MATSTAT',
        'credit_hours': 2,
        'enrollment': 490,
        'classes': ['CS200', 'IT200', 'OP200'],
        'lecturers': ['Dr. Bayes'],
        'requires_lab': False
    },
    'Stat350': {
        'title': 'Probability Theory',
        'type': 'lecture',
        'dept': 'MATSTAT',
        'credit_hours': 3,
        'enrollment': 550,
        'classes': ['CS300', 'IT300'],
        'lecturers': ['Dr. Euler'],
        'requires_lab': False
    },
    'Psych150': {
        'title': 'Introduction to Psychology',
        'type': 'lecture',
        'dept': 'PSYCH',
        'credit_hours': 2,
        'enrollment': 730,
        'classes': ['CS100', 'OP100', 'BS100', 'IT100'],
        'lecturers': ['Dr. Freud', 'Dr. Jung'],
        'requires_lab': False
    },
    'Physics202': {
        'title': 'Modern Physics',
        'type': 'lecture',
        'dept': 'PHYS',
        'credit_hours': 2,
        'enrollment': 365,
        'classes': ['CHEM200', 'BIOCHEM200', 'PHYS200'],
        'lecturers': ['Dr. Newton'],
        'requires_lab': False
    },
    'Chem101': {
        'title': 'Chemistry for Life Sciences',
        'type': 'lecture',
        'dept': 'CHEM',
        'credit_hours': 2,
        'enrollment': 240,
        'classes': ['CHEM100', 'BIOCHEM100'],
        'lecturers': ['Dr. Curie'],
        'requires_lab': False
    },
    'Bio301': {
        'title': 'Genetics and Evolution',
        'type': 'lecture',
        'dept': 'BS',
        'credit_hours': 3,
        'enrollment': 165,
        'classes': ['BIOCHEM300'],
        'lecturers': ['Dr. Darwin'],
        'requires_lab': False
    },
    'History102': {
        'title': 'World History',
        'type': 'lecture',
        'dept': 'HISTPOL',
        'credit_hours': 2,
        'enrollment': 430,
        'classes': ['CS400', 'OP300', 'BS300'],
        'lecturers': ['Dr. Herodotus'],
        'requires_lab': False
    },
    'Econs205': {
        'title': 'Principles of Economics',
        'type': 'lecture',
        'dept': 'ECONS',
        'credit_hours': 3,
        'enrollment': 100,
        'classes': ['BS200'],
        'lecturers': ['Dr. Keynes'],
        'requires_lab': False
    },
    'Geo110': {
        'title': 'Physical Geography',
        'type': 'lecture',
        'dept': 'GEOG',
        'credit_hours': 2,
        'enrollment': 120,
        'classes': ['PHYS300'],
        'lecturers': ['Dr. Humboldt'],
        'requires_lab': False
    }
}
           
        

        for code, data in courses_data.items():
            try:
                course_type = CourseType.objects.get(name=data['type'])
                department = Department.objects.get(code=data['dept'])
                lab_type = LabType.objects.get(name=data['lab_type']) if data.get('lab_type') else None

                course, created = Course.objects.get_or_create(
                    code=code,
                    defaults={
                        'title': data['title'],
                        'course_type': course_type,
                        'department': department,
                        'credit_hours': data['credit_hours'],
                        'enrollment': data['enrollment'],
                        'requires_lab': data.get('requires_lab', False),
                        'lab_type': lab_type
                    }
                )

                # Add classes
                for class_code in data['classes']:
                    cls = Class.objects.get(code=class_code)
                    course.classes.add(cls)

                # Add lecturers
                for lecturer_name in data['lecturers']:
                    lecturer = Lecturer.objects.get(name=lecturer_name)
                    course.lecturers.add(lecturer)

                self.stdout.write(f"✓ Course {code} loaded")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Error loading {code}: {str(e)}"))

    def load_proctor_assignments(self):
        self.stdout.write("\n=== LOADING PROCTOR ASSIGNMENTS ===")
        
        proctors_availability = {
            'Dr. Smith': ['2025-05-01', '2025-05-02', '2025-05-03', '2025-05-04', '2025-05-06', '2025-05-08'],
            'Dr. Johnson': ['2025-05-02', '2025-05-04', '2025-05-07', '2025-05-09', '2025-05-10', '2025-05-12'],
            'Dr. Euler': ['2025-05-01', '2025-05-03', '2025-05-05', '2025-05-07', '2025-05-10', '2025-05-12'],
            'Dr. Newton': ['2025-05-02', '2025-05-04', '2025-05-06', '2025-05-08', '2025-05-10', '2025-05-11'],
            'Dr. Curie': ['2025-05-01', '2025-05-03', '2025-05-05', '2025-05-07', '2025-05-09', '2025-05-12'],
            'Dr. Darwin': ['2025-05-02', '2025-05-04', '2025-05-06', '2025-05-08', '2025-05-10', '2025-05-11'],
            'Dr. Moore': ['2025-05-01', '2025-05-03', '2025-05-05', '2025-05-06', '2025-05-07', '2025-05-08'],
            'Dr. Taylor': ['2025-05-01', '2025-05-03', '2025-05-06', '2025-05-09', '2025-05-10', '2025-05-12'],
            'Dr. Miller': ['2025-05-02', '2025-05-05', '2025-05-07', '2025-05-09', '2025-05-11', '2025-05-12'],
            'Dr. Thomas': ['2025-05-01', '2025-05-04', '2025-05-06', '2025-05-08', '2025-05-10', '2025-05-12'],
            'Prof. White': ['2025-05-01', '2025-05-03', '2025-05-05', '2025-05-07', '2025-05-09', '2025-05-11'],
            'Dr. Bayes': ['2025-05-02', '2025-05-05', '2025-05-07', '2025-05-08', '2025-05-10', '2025-05-11'],
            'Dr. Jackson': ['2025-05-01', '2025-05-03', '2025-05-06', '2025-05-08', '2025-05-09', '2025-05-11'],
            'Dr. Turing': ['2025-05-02', '2025-05-04', '2025-05-06', '2025-05-08', '2025-05-10', '2025-05-12'],
            'Dr. Anderson': ['2025-05-01', '2025-05-04', '2025-05-07', '2025-05-09', '2025-05-10', '2025-05-12'],
            'Prof. Davis': ['2025-05-01', '2025-05-03', '2025-05-06', '2025-05-08', '2025-05-10', '2025-05-12']
        }


        for proctor_name, dates in proctors_availability.items():
            try:
                proctor = Lecturer.objects.get(name=proctor_name, is_proctor=True)
                
                for date_str in dates:
                    exam_date = ExamDate.objects.get(date=date_str)
                    ProctorAssignment.objects.get_or_create(
                        proctor=proctor,
                        exam_date=exam_date,
                        defaults={'is_available': True}
                    )
                    self.stdout.write(f"✓ Assigned {proctor_name} to {date_str}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Error assigning {proctor_name}: {str(e)}"))