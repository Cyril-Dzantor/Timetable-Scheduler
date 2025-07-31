from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from Users.models import User, StudentProfile, LecturerProfile
from Timetable.models import Class, Lecturer, ClassStudent
from django.db import transaction

class Command(BaseCommand):
    help = 'Link existing students and lecturers to user accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--students',
            action='store_true',
            help='Create user accounts for existing students',
        )
        parser.add_argument(
            '--lecturers',
            action='store_true',
            help='Create user accounts for existing lecturers',
        )
        parser.add_argument(
            '--sample',
            type=int,
            default=5,
            help='Number of sample accounts to create (default: 5)',
        )

    def handle(self, *args, **options):
        if options['students']:
            self.create_student_accounts(options['sample'])
        elif options['lecturers']:
            self.create_lecturer_accounts(options['sample'])
        else:
            self.stdout.write(
                self.style.ERROR('Please specify --students or --lecturers')
            )

    def create_student_accounts(self, sample_count):
        """Create user accounts for existing students"""
        self.stdout.write("Creating student user accounts...")
        
        # Get existing class-student relationships
        class_students = ClassStudent.objects.select_related('assigned_class').all()
        
        created_count = 0
        for class_student in class_students[:sample_count]:  # Limit to sample count
            try:
                with transaction.atomic():
                    # Generate email from index number
                    email = f"{class_student.student_index.lower()}@knust.edu.gh"
                    
                    # Check if user already exists
                    if User.objects.filter(email=email).exists():
                        self.stdout.write(f"User {email} already exists, skipping...")
                        continue
                    
                    # Create user
                    user = User.objects.create(
                        email=email,
                        username=email,
                        password=make_password('student123'),
                        is_student=True,
                        first_name=class_student.student_index.split('-')[0],
                        last_name=f"Student{created_count + 1}"
                    )
                    
                    # Create student profile
                    StudentProfile.objects.create(
                        user=user,
                        index_number=class_student.student_index,
                        program=f"{class_student.assigned_class.department.name}",
                        level=str(class_student.assigned_class.level),
                        assigned_class=class_student.assigned_class
                    )
                    
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ Created student account: {email} (Class: {class_student.assigned_class.code})"
                        )
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ Error creating student account: {e}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(f"Created {created_count} student accounts")
        )

    def create_lecturer_accounts(self, sample_count):
        """Create user accounts for existing lecturers"""
        self.stdout.write("Creating lecturer user accounts...")
        
        # Get existing lecturers
        lecturers = Lecturer.objects.all()
        
        created_count = 0
        for lecturer in lecturers[:sample_count]:  # Limit to sample count
            try:
                with transaction.atomic():
                    # Generate email from lecturer name
                    name_parts = lecturer.name.replace('Dr. ', '').replace('Prof. ', '').split()
                    first_name = name_parts[0].lower()
                    last_name = name_parts[-1].lower() if len(name_parts) > 1 else first_name
                    email = f"{first_name}.{last_name}@knust.edu.gh"
                    
                    # Check if user already exists
                    if User.objects.filter(email=email).exists():
                        self.stdout.write(f"User {email} already exists, skipping...")
                        continue
                    
                    # Create user
                    user = User.objects.create(
                        email=email,
                        username=email,
                        password=make_password('lecturer123'),
                        is_lecturer=True,
                        first_name=name_parts[0],
                        last_name=name_parts[-1] if len(name_parts) > 1 else name_parts[0]
                    )
                    
                    # Create lecturer profile
                    LecturerProfile.objects.create(
                        user=user,
                        staff_id=f"L{created_count + 1:03d}",
                        department=lecturer.department.name,
                        lecturer=lecturer
                    )
                    
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ Created lecturer account: {email} (Lecturer: {lecturer.name})"
                        )
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ Error creating lecturer account: {e}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(f"Created {created_count} lecturer accounts")
        ) 