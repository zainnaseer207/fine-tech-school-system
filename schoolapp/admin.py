from django.contrib import admin
from .models import (
    Student, Attendance, Teacher, Staff, Notice, Event,
    Fee, Message, Fund, Result, Lecture,
)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("name", "roll_no", "class_name", "email", "user")
    search_fields = ("name", "roll_no", "email")
    list_filter = ("class_name",)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("student", "date", "status")
    list_filter = ("status", "date")

@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    list_display = ("subject", "class_name", "teacher", "day_of_week", "start_time", "end_time", "room")
    list_filter = ("day_of_week", "class_name")


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("name", "subject", "email", "basic_salary", "net_salary")
    search_fields = ("name", "subject", "email")


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ("name", "designation", "department", "employee_id", "contact")
    search_fields = ("name", "employee_id", "department")


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ("title", "date")
    ordering = ("-date",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "event_date")
    ordering = ("event_date",)


@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ("student", "amount", "status", "date")
    list_filter = ("status",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "date", "read")
    list_filter = ("read",)


@admin.register(Fund)
class FundAdmin(admin.ModelAdmin):
    list_display = ("title", "fund_type", "amount", "date")
    list_filter = ("fund_type",)


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ("student", "subject", "marks_obtained", "total_marks", "grade")
    list_filter = ("subject",)
