import json
import numpy as np
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

# ---------- Academic Year ----------
class AcademicYear(models.Model):
    name = models.CharField(max_length=20, unique=True)          # e.g. "2025-2026"
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_current:
            # Ensure only one current academic year
            AcademicYear.objects.filter(is_current=True).update(is_current=False)
        super().save(*args, **kwargs)

# ---------- Course ----------
class Course(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    course_type = models.CharField(max_length=2, choices=[('UG', 'UG'), ('PG', 'PG')], default='UG')
    duration_years = models.IntegerField(default=3)   # total years

    def __str__(self):
        return f"{self.code} - {self.name}"

# ---------- Subject ----------
class Subject(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.IntegerField()   # 1,2,3,...

    class Meta:
        unique_together = ['code', 'course', 'semester']

    def __str__(self):
        return f"{self.code} - {self.name}"

# ---------- Section ----------
class Section(models.Model):
    name = models.CharField(max_length=10)          # e.g. "A", "B"
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.IntegerField()                # which semester this section belongs to

    class Meta:
        unique_together = ['name', 'course', 'semester']

    def __str__(self):
        return f"Section {self.name}"

# ---------- Custom User ----------
class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('principal', 'Principal'),
        ('hod', 'HOD'),
        ('lecturer', 'Lecturer'),
        ('student', 'Student'),
        ('staff', 'Non‑Teaching Staff'),
        ('admin', 'Admin'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    assigned_course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hod_user'
    )

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.user_type})"

# ---------- Student Profile ----------
class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    roll_no = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    face_encoding = models.TextField(blank=True, null=True)
    face_image = models.ImageField(upload_to='face_images/', blank=True, null=True)
    registration_complete = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.roll_no} - {self.user.get_full_name()}"

    def set_face_encoding(self, encoding_array):
        if isinstance(encoding_array, np.ndarray):
            self.face_encoding = json.dumps(encoding_array.tolist())

    def get_face_encoding(self):
        if self.face_encoding:
            return np.array(json.loads(self.face_encoding))
        return None

# ---------- Student Enrollment ----------
class StudentEnrollment(models.Model):
    LANGUAGE_CHOICES = (
        ('KAN', 'Kannada'),
        ('HIN', 'Hindi'),
    )
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, null=True, blank=True)
    semester = models.IntegerField()          # 1,2,3...
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    subjects = models.ManyToManyField(Subject)
    language1 = models.CharField(max_length=3, choices=LANGUAGE_CHOICES, default='KAN')
    # language2 is always Basic English – assigned automatically during enrollment creation

    class Meta:
        unique_together = ['student', 'course', 'semester']   # one enrollment per semester per course

    def __str__(self):
        return f"{self.student.roll_no} - {self.course.code} Sem {self.semester}"

# ---------- Staff Profile ----------
class StaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    employee_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    face_encoding = models.TextField(blank=True, null=True)
    face_image = models.ImageField(upload_to='staff_faces/', blank=True, null=True)
    registration_complete = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.employee_id or 'No ID'}"

    def set_face_encoding(self, encoding_array):
        if isinstance(encoding_array, np.ndarray):
            self.face_encoding = json.dumps(encoding_array.tolist())

    def get_face_encoding(self):
        if self.face_encoding:
            return np.array(json.loads(self.face_encoding))
        return None

# ---------- Lecturer Subject Allocation ----------
class LecturerAllocation(models.Model):
    lecturer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'lecturer'}
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    semester = models.IntegerField()
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="If blank, applies to all sections"
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['lecturer', 'course', 'academic_year', 'semester', 'section', 'subject']

    def __str__(self):
        section_name = self.section.name if self.section else "All Sections"
        return f"{self.lecturer.username} - {self.subject.code} ({self.course.code} Sem {self.semester} {section_name})"