from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from Users.models import User, StudentProfile, LecturerProfile
from Timetable.models import Class, Lecturer
from django.db import transaction

class Command(BaseCommand):
    help = 'Set up student and lecturer accounts with proper relationships'

    def add_arguments(self, parser):
        parser.add_argument(
            '--student',
            action='store_true',
            help='Create a student account',
        )
        parser.add_argument(
            '--lecturer',
            action='store_true',
            help='Create a lecturer account',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email for the account',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='password123',
            help='Password for the account (default: password123)',
        )
        parser.add_argument(
            '--index-number',
            type=str,
            help='Index number for student',
        )
        parser.add_argument(
            '--staff-id',
            type=str,
            help='Staff ID for lecturer',
        )
        parser.add_argument(
            '--class-code',
            type=str,
            help='Class code to assign to student',
        )
        parser.add_argument(
            '--lecturer-name',
            type=str,
            help='Lecturer name to link to lecturer account',
        )

    def handle(self, *args, **options):
        if options['student']:
            self.create_student_account(options)
        elif options['lecturer']:
            self.create_lecturer_account(options)
        else:
            self.stdout.write(
                self.style.ERROR('Please specify --student or --lecturer')
            )

    def create_student_account(self, options):
        email = options['email']
        password = options['password']
        index_number = options['index_number']
        class_code = options['class_code']

        if not all([email, index_number, class_code]):
            self.stdout.write(
                self.style.ERROR('Please provide --email, --index-number, and --class-code for student')
            )
            return

        try:
            with transaction.atomic():
                # Create user
                user = User.objects.create(
                    email=email,
                    username=email,
                    password=make_password(password),
                    is_student=True,
                    first_name=email.split('@')[0].split('.')[0].title(),
                    last_name=email.split('@')[0].split('.')[1].title() if '.' in email.split('@')[0] else ''
                )

                # Get class
                try:
                    class_obj = Class.objects.get(code=class_code)
                except Class.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'Class with code {class_code} does not exist')
                    )
                    return

                # Create student profile
                StudentProfile.objects.create(
                    user=user,
                    index_number=index_number,
                    program=f"{class_obj.department.name}",
                    level=str(class_obj.level),
                    assigned_class=class_obj
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Student account created successfully!\n'
                        f'Email: {email}\n'
                        f'Password: {password}\n'
                        f'Index Number: {index_number}\n'
                        f'Class: {class_code}'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating student account: {e}')
            )

    def create_lecturer_account(self, options):
        email = options['email']
        password = options['password']
        staff_id = options['staff_id']
        lecturer_name = options['lecturer_name']

        if not all([email, staff_id, lecturer_name]):
            self.stdout.write(
                self.style.ERROR('Please provide --email, --staff-id, and --lecturer-name for lecturer')
            )
            return

        try:
            with transaction.atomic():
                # Create user
                user = User.objects.create(
                    email=email,
                    username=email,
                    password=make_password(password),
                    is_lecturer=True,
                    first_name=lecturer_name.split()[0] if ' ' in lecturer_name else lecturer_name,
                    last_name=lecturer_name.split()[1] if ' ' in lecturer_name else ''
                )

                # Get lecturer
                try:
                    lecturer_obj = Lecturer.objects.get(name=lecturer_name)
                except Lecturer.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'Lecturer with name {lecturer_name} does not exist')
                    )
                    return

                # Create lecturer profile
                LecturerProfile.objects.create(
                    user=user,
                    staff_id=staff_id,
                    department=lecturer_obj.department.name,
                    lecturer=lecturer_obj
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Lecturer account created successfully!\n'
                        f'Email: {email}\n'
                        f'Password: {password}\n'
                        f'Staff ID: {staff_id}\n'
                        f'Lecturer: {lecturer_name}'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating lecturer account: {e}')
            ) 