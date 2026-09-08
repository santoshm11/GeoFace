from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    AcademicYear, Course, Subject, Section, User,
    StudentProfile, StudentEnrollment, StaffProfile, LecturerAllocation
)

# ---------- AcademicYear ----------
@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_current')
    list_filter = ('is_current',)
    search_fields = ('name',)

# ---------- Course ----------
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'department', 'course_type', 'duration_years')
    search_fields = ('code', 'name')
    list_filter = ('course_type', 'department')

# ---------- Subject ----------
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'course', 'semester')
    search_fields = ('code', 'name')
    list_filter = ('course', 'semester')

# ---------- Section ----------
@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'semester')
    search_fields = ('name',)
    list_filter = ('course', 'semester')

# ---------- User (custom) ----------
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username', 'first_name', 'last_name', 'email',
        'user_type', 'assigned_course', 'is_staff', 'is_active'
    )
    list_filter = ('user_type', 'is_staff', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')

    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone_number', 'assigned_course')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone_number', 'assigned_course')}),
    )

# ---------- StudentProfile ----------
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'roll_no', 'department', 'registration_complete')
    search_fields = ('roll_no', 'user__first_name', 'user__last_name', 'user__username')
    list_filter = ('department', 'registration_complete')
    readonly_fields = ('face_encoding',)

# ---------- StudentEnrollment ----------
@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'academic_year', 'semester', 'section', 'language1')
    search_fields = ('student__roll_no', 'student__user__first_name', 'student__user__last_name')
    list_filter = ('course', 'academic_year', 'semester', 'section', 'language1')
    filter_horizontal = ('subjects',)

# ---------- StaffProfile ----------
@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_id', 'department', 'designation', 'registration_complete')
    search_fields = ('employee_id', 'user__first_name', 'user__last_name', 'user__username')
    list_filter = ('department', 'designation', 'registration_complete')
    readonly_fields = ('face_encoding',)

# ---------- LecturerAllocation ----------
@admin.register(LecturerAllocation)
class LecturerAllocationAdmin(admin.ModelAdmin):
    list_display = ('lecturer', 'course', 'academic_year', 'semester', 'section', 'subject')
    search_fields = ('lecturer__username', 'lecturer__first_name', 'subject__code', 'course__code')
    list_filter = ('course', 'academic_year', 'semester', 'section', 'subject')