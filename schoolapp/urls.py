from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path("", views.login_view, name="login"),     # root goes to login
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_view, name="logout"),

    # Dashboard
    path("dashboard/", views.dashboard, name="dashboard"),

    # Students
    path("students/", views.students_list, name="students"), 
    path("students/add/", views.add_student, name="add_student"),
    path("students/edit/<int:id>/", views.edit_student, name="edit_student"),
    path("students/delete/<int:id>/", views.delete_student, name="delete_student"),

    # Teachers
    path("teachers/", views.teachers_list, name="teachers"),
    path("teachers/add/", views.add_teacher, name="add_teacher"),
    path("teachers/edit/<int:id>/", views.edit_teacher, name="edit_teacher"),
    path("teachers/delete/<int:id>/", views.delete_teacher, name="delete_teacher"),

    # Staff
    path("staff/", views.staff_list, name="staff"),
    path("staff/add/", views.add_staff, name="add_staff"),
    path("staff/edit/<int:id>/", views.edit_staff, name="edit_staff"),
    path("staff/delete/<int:id>/", views.delete_staff, name="delete_staff"),

    # Notices
    path("notices/", views.notices_list, name="notices"),
    path("notices/add/", views.add_notice, name="add_notice"),
    path("notices/delete/<int:id>/", views.delete_notice, name="delete_notice"),

    # Events
    path("events/", views.events_list, name="events"),
    path("events/add/", views.add_event, name="add_event"),
    path("events/delete/<int:id>/", views.delete_event, name="delete_event"),

    # Fees
    path("fees/", views.fees_list, name="fees"),
    path("fees/add/", views.add_fee, name="add_fee"),

    # Messages
    path("messages/", views.messages_list, name="messages"),
    path("messages/read/<int:id>/", views.mark_read, name="mark_read"),

    # Attendance
    path("attendance/pdf/", views.attendance_pdf, name="attendance_pdf"),
    path("attendance/", views.attendance_view, name="attendance"),
    path("attendance/pdf/", views.attendance_pdf, name="attendance_pdf"),

    # Lectures
    path("lectures/", views.lectures_list, name="lectures"),
    path("lectures/add/", views.add_lecture, name="add_lecture"),
    path("lectures/edit/<int:id>/", views.edit_lecture, name="edit_lecture"),
    path("lectures/delete/<int:id>/", views.delete_lecture, name="delete_lecture"),

    # Funds
    path("funds/", views.funds_list, name="funds"),
    path("funds/add/", views.add_fund, name="add_fund"),
    path("funds/edit/<int:id>/", views.edit_fund, name="edit_fund"),
    path("funds/delete/<int:id>/", views.delete_fund, name="delete_fund"),

    # Fee Voucher
    path("fee-voucher/select/", views.select_student_fee, name="select_student_fee"),
    path("fee-voucher/<int:student_id>/", views.generate_fee_voucher, name="generate_fee_voucher"),

    # Salary Slip
    path("salary-slip/select/", views.select_teacher_salary, name="select_teacher_salary"),
    path("salary-slip/<int:teacher_id>/", views.generate_salary_slip, name="generate_salary_slip"),
    
    # Staff Salary Slip
    path("salary-slip/staff/select/", views.select_staff_salary, name="select_staff_salary"),
    path("salary-slip/staff/<int:staff_id>/", views.generate_staff_salary_slip, name="generate_staff_salary_slip"),

    # Result Card
    path("result-card/select/", views.select_student_result, name="select_student_result"),
    path("result-card/<int:student_id>/", views.generate_result_card, name="generate_result_card"),

    # Edit & Download
    path("edit-result/<int:student_id>/", views.edit_result, name="edit_result_card"),
    path("edit-salary/<int:pk>/", views.edit_salary, name="edit_salary"),
    path("download/result-card/<int:student_id>/", views.download_result_card, name="download_result_card"),
    path("download/salary-slip/<int:teacher_id>/", views.download_salary_slip, name="download_salary_slip"),
]
