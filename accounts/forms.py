from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import (
    StudentProfile, Course, Section, StaffProfile,
    AcademicYear, StudentEnrollment, Subject, LecturerAllocation
)

User = get_user_model()

# ---------- Helper: get current academic year ----------
def get_current_academic_year():
    try:
        return AcademicYear.objects.get(is_current=True)
    except AcademicYear.DoesNotExist:
        return None

# ---------- Admin User Create ----------
class AdminUserCreateForm(UserCreationForm):
    user_type = forms.ChoiceField(choices=User.USER_TYPE_CHOICES)
    phone_number = forms.CharField(max_length=15, required=False)
    assigned_course = forms.ModelChoiceField(queryset=Course.objects.all(), required=False)

    class Meta:
        model = User
        fields = (
            'username', 'first_name', 'last_name', 'email', 'phone_number',
            'user_type', 'assigned_course', 'password1', 'password2'
        )

# ---------- Admin User Update ----------
class AdminUserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            'username', 'first_name', 'last_name', 'email', 'phone_number',
            'user_type', 'assigned_course', 'is_active'
        )

# ---------- Student Profile Form ----------
class StudentProfileForm(forms.ModelForm):
    course = forms.ModelChoiceField(queryset=Course.objects.all())
    semester = forms.IntegerField(min_value=1)
    section = forms.ModelChoiceField(queryset=Section.objects.all())
    roll_no = forms.CharField(max_length=20)
    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        required=False,
        help_text="Leave blank to use current academic year"
    )

    class Meta:
        model = StudentProfile
        fields = ('roll_no', 'department', 'face_image')

# ---------- Staff Profile Forms ----------
class StaffProfileForm(forms.ModelForm):
    designation = forms.ChoiceField(
        choices=[('', '--------')] + [(d, d) for d in ['FDA', 'SDA', 'Peon', 'Lab Attender', 'Sweeper']],
        required=False
    )

    class Meta:
        model = StaffProfile
        fields = ('employee_id', 'department', 'designation', 'face_image')
        widgets = {
            'face_image': forms.FileInput(attrs={'accept': 'image/*'}),
        }

class TeachingStaffProfileForm(forms.ModelForm):
    designation = forms.ChoiceField(
        choices=[
            ('', '--------'),
            ('Professor', 'Professor'),
            ('Associate Professor', 'Associate Professor'),
            ('Assistant Professor', 'Assistant Professor'),
            ('Lecturer/Instructor', 'Lecturer/Instructor')
        ],
        required=False
    )

    class Meta:
        model = StaffProfile
        fields = ('employee_id', 'department', 'designation', 'face_image')
        widgets = {
            'face_image': forms.FileInput(attrs={'accept': 'image/*'}),
        }

class NonTeachingStaffProfileForm(forms.ModelForm):
    designation = forms.ChoiceField(
        choices=[('', '--------')] + [
            ('FDA', 'FDA'),
            ('SDA', 'SDA'),
            ('Peon', 'Peon'),
            ('Lab Attender', 'Lab Attender'),
            ('Sweeper', 'Sweeper')
        ],
        required=False
    )

    class Meta:
        model = StaffProfile
        fields = ('employee_id', 'department', 'designation', 'face_image')
        widgets = {
            'face_image': forms.FileInput(attrs={'accept': 'image/*'}),
        }

# ---------- Bulk Upload ----------
class BulkUploadForm(forms.Form):
    user_type = forms.ChoiceField(choices=[
        ('student', 'Student'),
        ('lecturer', 'Teaching Staff'),
        ('staff', 'Non-Teaching Staff')
    ])
    excel_file = forms.FileField(label='Excel File (.xlsx)')

# ---------- Student Registration (single) ----------
class StudentRegistrationForm(forms.Form):
    student_name = forms.CharField(max_length=100, label="Student Name")
    uucms_id = forms.CharField(max_length=20, label="UUCMS ID")
    email = forms.EmailField(label="Email")
    phone_number = forms.CharField(max_length=15, required=False, label="Phone Number")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")

    face_image = forms.ImageField(required=False, label="Face Image")

    course = forms.ModelChoiceField(queryset=Course.objects.all().order_by('code'), label="Course")
    semester = forms.ChoiceField(
        choices=[(1, '1'), (3, '3'), (5, '5')],
        label="Semester",
        initial=1,
    )
    section = forms.ModelChoiceField(queryset=Section.objects.none(), label="Section")
    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        required=False,
        label="Academic Year",
        help_text="Leave blank to use current academic year"
    )

    LANGUAGE_CHOICES = [('KAN', 'Kannada'), ('HIN', 'Hindi')]
    language1 = forms.ChoiceField(choices=LANGUAGE_CHOICES, label="Language 1")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'course' in self.data and 'semester' in self.data:
            try:
                course_id = int(self.data.get('course'))
                semester = int(self.data.get('semester'))
                self.fields['section'].queryset = Section.objects.filter(course_id=course_id, semester=semester)
            except (ValueError, TypeError):
                pass
        else:
            self.fields['section'].queryset = Section.objects.none()

        # Set default academic year to current if not provided
        if not self.initial.get('academic_year'):
            current = get_current_academic_year()
            if current:
                self.initial['academic_year'] = current

    def clean_face_image(self):
        face_image = self.cleaned_data.get('face_image')
        if face_image:
            from attendance.utils import encode_face_from_image
            encoding = encode_face_from_image(face_image)
            if encoding is None:
                raise forms.ValidationError(
                    "No face detected in the image. Please upload a clear frontal face photo."
                )
            self._face_encoding = encoding
        return face_image

    def clean_uucms_id(self):
        uucms_id = self.cleaned_data.get('uucms_id')
        if User.objects.filter(username=uucms_id).exists():
            raise forms.ValidationError("This UUCMS ID is already registered.")
        return uucms_id

    def clean_student_name(self):
        name = self.cleaned_data.get('student_name').strip()
        if not name:
            raise forms.ValidationError("Student name is required.")
        return name

    def clean_academic_year(self):
        year = self.cleaned_data.get('academic_year')
        if not year:
            current = get_current_academic_year()
            if current:
                return current
            raise forms.ValidationError("No academic year selected and no current year set.")
        return year

    def save(self, commit=True):
        data = self.cleaned_data
        with transaction.atomic():
            user = User.objects.create_user(
                username=data['uucms_id'],
                password=data['password'],
                first_name=data['student_name'],
                last_name='',
                email=data['email'],
                phone_number=data.get('phone_number', ''),
                user_type='student'
            )
            student_profile = StudentProfile.objects.create(
                user=user,
                roll_no=data['uucms_id'],
                department=data['course'].department,
                registration_complete=False
            )
            # Handle face image (if provided)
            if data.get('face_image'):
                from attendance.utils import encode_face_from_image
                from django.core.files.base import ContentFile
                # Save image and encoding
                student_profile.face_image = data['face_image']
                student_profile.save(update_fields=['face_image'])
                encoding = encode_face_from_image(student_profile.face_image.path)
                if encoding is not None:
                    student_profile.set_face_encoding(encoding)
                    student_profile.registration_complete = True
                    student_profile.save(update_fields=['face_encoding', 'registration_complete'])

            # Create enrollment with language1
            enrollment = StudentEnrollment(
                student=student_profile,
                course=data['course'],
                academic_year=data['academic_year'],
                semester=int(data['semester']),
                section=data['section'],
                language1=data['language1'],
            )
            enrollment.save()

            # Assign subjects (core, language1, language2)
            from attendance.utils import get_mandatory_subjects, get_language_subject, get_english_subject
            core = get_mandatory_subjects(data['course'], int(data['semester']), data['section'])
            lang1 = get_language_subject(data['course'], int(data['semester']), data['language1'])
            lang2 = get_english_subject(data['course'], int(data['semester']))
            all_subjects = list(core) + [lang1, lang2]
            enrollment.subjects.add(*all_subjects)

            return user

# ---------- Teaching Staff Registration ----------
class TeachingStaffRegistrationForm(forms.Form):
    full_name = forms.CharField(max_length=100, label="Full Name")
    username = forms.CharField(max_length=150, label="Employee ID")
    email = forms.EmailField(label="Email")
    phone_number = forms.CharField(max_length=15, required=False, label="Phone Number")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    course = forms.ModelChoiceField(queryset=Course.objects.all(), label="Course")
    designation = forms.ChoiceField(
        choices=[
            ('', 'Select Designation'),
            ('Professor', 'Professor'),
            ('Associate Professor', 'Associate Professor'),
            ('Assistant Professor', 'Assistant Professor'),
            ('Lecturer/Instructor', 'Lecturer/Instructor'),
        ],
        label="Designation"
    )
    face_image = forms.ImageField(required=False, label="Face Image")

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This Employee ID is already registered.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def save(self, commit=True):
        data = self.cleaned_data
        with transaction.atomic():
            user = User.objects.create_user(
                username=data['username'],
                password=data['password'],
                first_name=data['full_name'],
                last_name='',
                email=data['email'],
                phone_number=data.get('phone_number', ''),
                user_type='lecturer',
                assigned_course=data['course']  # only if this lecturer is also HOD? but store anyway
            )
            staff_profile = StaffProfile.objects.create(
                user=user,
                employee_id=data['username'],
                department=data['course'].name,
                designation=data['designation'],
                registration_complete=False
            )
            if data.get('face_image'):
                from attendance.utils import encode_face_from_image
                staff_profile.face_image = data['face_image']
                staff_profile.save(update_fields=['face_image'])
                encoding = encode_face_from_image(staff_profile.face_image.path)
                if encoding is not None:
                    staff_profile.set_face_encoding(encoding)
                    staff_profile.registration_complete = True
                    staff_profile.save(update_fields=['face_encoding', 'registration_complete'])
            return user

# ---------- Non-Teaching Staff Registration ----------
class NonTeachingStaffRegistrationForm(forms.Form):
    full_name = forms.CharField(max_length=100, label="Full Name")
    username = forms.CharField(max_length=150, label="Employee ID")
    email = forms.EmailField(label="Email")
    phone_number = forms.CharField(max_length=15, required=False, label="Phone Number")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    designation = forms.ChoiceField(choices=[
        ('', 'Select Designation'),
        ('FDA', 'FDA'),
        ('SDA', 'SDA'),
        ('Peon', 'Peon'),
        ('Lab Attender', 'Lab Attender'),
        ('Sweeper', 'Sweeper'),
    ], label="Designation")
    face_image = forms.ImageField(required=False, label="Face Image")

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This Employee ID is already registered.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def save(self, commit=True):
        data = self.cleaned_data
        with transaction.atomic():
            user = User.objects.create_user(
                username=data['username'],
                password=data['password'],
                first_name=data['full_name'],
                last_name='',
                email=data['email'],
                phone_number=data.get('phone_number', ''),
                user_type='staff'
            )
            staff_profile = StaffProfile.objects.create(
                user=user,
                employee_id=data['username'],
                department='',
                designation=data['designation'],
                registration_complete=False
            )
            if data.get('face_image'):
                from attendance.utils import encode_face_from_image
                staff_profile.face_image = data['face_image']
                staff_profile.save(update_fields=['face_image'])
                encoding = encode_face_from_image(staff_profile.face_image.path)
                if encoding is not None:
                    staff_profile.set_face_encoding(encoding)
                    staff_profile.registration_complete = True
                    staff_profile.save(update_fields=['face_encoding', 'registration_complete'])
            return user

# ---------- Lecturer Allocation Form (for master login) ----------
class LecturerAllocationForm(forms.ModelForm):
    class Meta:
        model = LecturerAllocation
        fields = ('lecturer', 'course', 'academic_year', 'semester', 'section', 'subject')
        widgets = {
            'section': forms.Select(attrs={'help_text': 'Leave blank for all sections'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit lecturer choices to user_type='lecturer'
        self.fields['lecturer'].queryset = User.objects.filter(user_type='lecturer')
        # Set academic_year default to current
        current = get_current_academic_year()
        if current:
            self.fields['academic_year'].initial = current
        # Dynamically filter sections based on course & semester (if present)
        if 'course' in self.data and 'semester' in self.data:
            try:
                course_id = int(self.data.get('course'))
                semester = int(self.data.get('semester'))
                self.fields['section'].queryset = Section.objects.filter(course_id=course_id, semester=semester)
            except (ValueError, TypeError):
                pass
        else:
            self.fields['section'].queryset = Section.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        lecturer = cleaned_data.get('lecturer')
        course = cleaned_data.get('course')
        academic_year = cleaned_data.get('academic_year')
        semester = cleaned_data.get('semester')
        section = cleaned_data.get('section')
        subject = cleaned_data.get('subject')

        if lecturer and course and academic_year and semester and subject:
            # Check for duplicate allocation
            qs = LecturerAllocation.objects.filter(
                lecturer=lecturer,
                course=course,
                academic_year=academic_year,
                semester=semester,
                subject=subject
            )
            if section:
                qs = qs.filter(section=section)
            else:
                qs = qs.filter(section__isnull=True)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("This allocation already exists for the selected lecturer, course, year, semester, and section.")
        return cleaned_data