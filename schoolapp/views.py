import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Sum
from django.forms import modelformset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from xhtml2pdf import pisa

from .forms import ResultForm, SalaryForm
from .models import (
    Attendance, Event, Fee, Fund, Message, Notice,
    Lecture, Result, Staff, Student, Teacher,
)

PDF_TABLE_STYLE = TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#14213d")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ("FONTSIZE", (0, 0), (-1, -1), 10),
    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ecf0f1")),
])


# ==================================================================
# Authentication
# ==================================================================

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard")
        messages.error(request, "Invalid username or password.")
        return redirect("login")
    return render(request, "login.html")


def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
        elif not username or not password:
            messages.error(request, "Username and password are required.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "That username is already taken.")
        elif email and User.objects.filter(email=email).exists():
            messages.error(request, "An account with that email already exists.")
        else:
            User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, "Account created successfully! You can log in now.")
            return redirect("login")

    return render(request, "signup.html")

@login_required(login_url="login")
def attendance_view(request):
    students = Student.objects.filter(user=request.user).order_by("class_name", "name")
    classes = students.values("class_name").annotate(total=Count("id")).order_by("class_name")
    today = datetime.date.today()

    if request.method == "POST":
        for student in students:
            status = request.POST.get(f"attendance_{student.id}")
            if status:
                Attendance.objects.update_or_create(
                    student=student, date=today, defaults={"status": status}
                )
        messages.success(request, f"Attendance saved for {today.strftime('%d %b %Y')}.")
        return redirect("attendance")

    todays_records = {
        a.student_id: a.status
        for a in Attendance.objects.filter(student__in=students, date=today)
    }

    return render(request, "attendance.html", {
        "students": students,
        "classes": classes,
        "today": today,
        "todays_records": todays_records,
    })

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


@login_required(login_url="login")
def lectures_list(request):
    lectures = Lecture.objects.select_related("teacher").all()
    classes = sorted(set(lectures.values_list("class_name", flat=True)))
    selected_class = request.GET.get("class_name", "")

    if selected_class:
        lectures = lectures.filter(class_name=selected_class)

    grouped = {day: [] for day in DAY_ORDER}
    for lec in lectures:
        grouped.setdefault(lec.day_of_week, []).append(lec)

    context = {
        "grouped": grouped,
        "day_order": DAY_ORDER,
        "classes": classes,
        "selected_class": selected_class,
    }
    return render(request, "lectures.html", context)


@login_required(login_url="login")
def add_lecture(request):
    teachers = Teacher.objects.all()

    if request.method == "POST":
        teacher_id = request.POST.get("teacher")
        day_of_week = request.POST.get("day_of_week")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")

        clash = Lecture.objects.filter(
            teacher_id=teacher_id, day_of_week=day_of_week,
            start_time__lt=end_time, end_time__gt=start_time,
        ).exists()

        if clash:
            messages.error(request, "This teacher already has a lecture scheduled that overlaps this time slot.")
        else:
            Lecture.objects.create(
                teacher_id=teacher_id,
                subject=request.POST.get("subject"),
                class_name=request.POST.get("class_name"),
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time,
                room=request.POST.get("room", ""),
            )
            messages.success(request, "Lecture scheduled successfully.")
            return redirect("lectures")

    return render(request, "add_lecture.html", {"teachers": teachers, "days": Lecture.DAY_CHOICES})


@login_required(login_url="login")
def edit_lecture(request, id):
    lecture = get_object_or_404(Lecture, id=id)
    teachers = Teacher.objects.all()

    if request.method == "POST":
        teacher_id = request.POST.get("teacher")
        day_of_week = request.POST.get("day_of_week")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")

        clash = Lecture.objects.filter(
            teacher_id=teacher_id, day_of_week=day_of_week,
            start_time__lt=end_time, end_time__gt=start_time,
        ).exclude(id=lecture.id).exists()

        if clash:
            messages.error(request, "This teacher already has a lecture scheduled that overlaps this time slot.")
        else:
            lecture.teacher_id = teacher_id
            lecture.subject = request.POST.get("subject")
            lecture.class_name = request.POST.get("class_name")
            lecture.day_of_week = day_of_week
            lecture.start_time = start_time
            lecture.end_time = end_time
            lecture.room = request.POST.get("room", "")
            lecture.save()
            messages.success(request, "Lecture updated successfully.")
            return redirect("lectures")

    return render(request, "edit_lecture.html", {"lecture": lecture, "teachers": teachers, "days": Lecture.DAY_CHOICES})


@login_required(login_url="login")
def delete_lecture(request, id):
    lecture = get_object_or_404(Lecture, id=id)
    if request.method == "POST":
        lecture.delete()
        messages.success(request, "Lecture removed from the timetable.")
        return redirect("lectures")
    return render(request, "delete_lecture.html", {"lecture": lecture})


def logout_view(request):
    logout(request)
    return redirect("login")


# ==================================================================
# Dashboard
# ==================================================================

@login_required(login_url="login")
def dashboard(request):
    students = Student.objects.all()
    teachers = Teacher.objects.all()
    staff = Staff.objects.all()

    today = datetime.date.today()
    total_students = students.count()
    today_attendance = Attendance.objects.filter(date=today, status="Present").count()
    attendance_percentage = (
        round((today_attendance / total_students) * 100, 2) if total_students > 0 else 0
    )

    notices = Notice.objects.order_by("-date")[:5]
    events = Event.objects.filter(event_date__gte=today).order_by("event_date")[:5]

    paid = Fee.objects.filter(status="Paid").count()
    pending = Fee.objects.filter(status="Pending").count()
    fee_percentage = round((paid / (paid + pending)) * 100, 2) if (paid + pending) > 0 else 0

    unread_messages = Message.objects.filter(read=False).count()

    total_income = Fund.objects.filter(fund_type="Income").aggregate(Sum("amount"))["amount__sum"] or 0
    total_expenditure = Fund.objects.filter(fund_type="Expenditure").aggregate(Sum("amount"))["amount__sum"] or 0
    balance = total_income - total_expenditure

    context = {
        "students": students,
        "teachers": teachers,
        "staff": staff,
        "attendance_percentage": f"{attendance_percentage}%",
        "notices": notices,
        "events": events,
        "fee_percentage": f"{fee_percentage}%",
        "unread_messages": unread_messages,
        "total_income": total_income,
        "total_expenditure": total_expenditure,
        "balance": balance,
    }
    return render(request, "dashboard.html", context)


# ==================================================================
# Students
# ==================================================================

@login_required(login_url="login")
def students_list(request):
    students = Student.objects.filter(user=request.user)
    classes = students.values("class_name").annotate(total=Count("id"))

    if request.method == "POST":
        today = datetime.date.today()
        for student in students:
            status = request.POST.get(f"attendance_{student.id}")
            if status:
                Attendance.objects.update_or_create(
                    student=student, date=today, defaults={"status": status}
                )
        return redirect("students")

    return render(request, "students.html", {"students": students, "classes": classes})


@login_required(login_url="login")
def add_student(request):
    if request.method == "POST":
        Student.objects.create(
            user=request.user,
            name=request.POST.get("name"),
            father_name=request.POST.get("father_name"),
            roll_no=request.POST.get("roll_no"),
            class_name=request.POST.get("class_name"),
            email=request.POST.get("email"),
        )
        return redirect("students")
    return render(request, "add_student.html")


@login_required(login_url="login")
def edit_student(request, id):
    student = get_object_or_404(Student, id=id)
    if request.method == "POST":
        student.name = request.POST.get("name")
        student.father_name = request.POST.get("father_name")
        student.roll_no = request.POST.get("roll_no")
        student.class_name = request.POST.get("class_name")
        student.email = request.POST.get("email")
        student.save()
        return redirect("students")
    return render(request, "edit_student.html", {"student": student})


@login_required(login_url="login")
def delete_student(request, id):
    student = get_object_or_404(Student, id=id)
    if request.method == "POST":
        student.delete()
        return redirect("students")
    return render(request, "delete_student.html", {"student": student})


# ==================================================================
# Teachers
# ==================================================================

@login_required(login_url="login")
def teachers_list(request):
    teachers = Teacher.objects.all()
    return render(request, "teachers.html", {"teachers": teachers})


@login_required(login_url="login")
def add_teacher(request):
    if request.method == "POST":
        Teacher.objects.create(
            user=request.user,
            name=request.POST.get("name"),
            subject=request.POST.get("subject"),
            email=request.POST.get("email"),
        )
        return redirect("teachers")
    return render(request, "add_teacher.html")


@login_required(login_url="login")
def edit_teacher(request, id):
    teacher = get_object_or_404(Teacher, id=id)
    if request.method == "POST":
        teacher.name = request.POST.get("name")
        teacher.subject = request.POST.get("subject")
        teacher.email = request.POST.get("email")
        teacher.save()
        return redirect("teachers")
    return render(request, "edit_teacher.html", {"teacher": teacher})


@login_required(login_url="login")
def delete_teacher(request, id):
    teacher = get_object_or_404(Teacher, id=id)
    if request.method == "POST":
        teacher.delete()
        return redirect("teachers")
    return render(request, "delete_teacher.html", {"teacher": teacher})


# ==================================================================
# Staff
# ==================================================================

@login_required(login_url="login")
def staff_list(request):
    staff_members = Staff.objects.all()
    return render(request, "staff.html", {"staff": staff_members})


@login_required(login_url="login")
def add_staff(request):
    if request.method == "POST":
        Staff.objects.create(
            user=request.user,
            name=request.POST.get("name"),
            employee_id=request.POST.get("employee_id"),
            designation=request.POST.get("designation"),
            department=request.POST.get("department"),
            contact=request.POST.get("contact"),
        )
        return redirect("staff")
    return render(request, "add_staff.html")


@login_required(login_url="login")
def edit_staff(request, id):
    staff = get_object_or_404(Staff, id=id)
    if request.method == "POST":
        staff.name = request.POST.get("name")
        staff.employee_id = request.POST.get("employee_id")
        staff.designation = request.POST.get("designation")
        staff.department = request.POST.get("department")
        staff.contact = request.POST.get("contact")
        staff.save()
        return redirect("staff")
    return render(request, "edit_staff.html", {"staff": staff})


@login_required(login_url="login")
def delete_staff(request, id):
    staff = get_object_or_404(Staff, id=id)
    if request.method == "POST":
        staff.delete()
        return redirect("staff")
    return render(request, "delete_staff.html", {"staff": staff})


# ==================================================================
# Notices
# ==================================================================

@login_required(login_url="login")
def notices_list(request):
    notices = Notice.objects.all().order_by("-date")
    return render(request, "notices.html", {"notices": notices})


@login_required(login_url="login")
def add_notice(request):
    if request.method == "POST":
        Notice.objects.create(
            title=request.POST["title"], description=request.POST["description"]
        )
        return redirect("notices")
    return render(request, "add_notice.html")


@login_required(login_url="login")
def delete_notice(request, id):
    notice = get_object_or_404(Notice, id=id)
    if request.method == "POST":
        notice.delete()
    return redirect("notices")


# ==================================================================
# Events
# ==================================================================

@login_required(login_url="login")
def events_list(request):
    events = Event.objects.all().order_by("event_date")
    return render(request, "events.html", {"events": events})


@login_required(login_url="login")
def add_event(request):
    if request.method == "POST":
        Event.objects.create(
            title=request.POST["title"],
            description=request.POST["description"],
            event_date=request.POST["event_date"],
        )
        return redirect("events")
    return render(request, "add_event.html")


@login_required(login_url="login")
def delete_event(request, id):
    event = get_object_or_404(Event, id=id)
    if request.method == "POST":
        event.delete()
    return redirect("events")


# ==================================================================
# Fees
# ==================================================================

@login_required(login_url="login")
def fees_list(request):
    fees = Fee.objects.select_related("student").all()
    return render(request, "fees.html", {"fees": fees})


@login_required(login_url="login")
def add_fee(request):
    if request.method == "POST":
        Fee.objects.create(
            student_id=request.POST["student"],
            amount=request.POST["amount"],
            status=request.POST["status"],
        )
        return redirect("fees")
    students = Student.objects.all()
    return render(request, "add_fee.html", {"students": students})


# ==================================================================
# Messages
# ==================================================================

@login_required(login_url="login")
def messages_list(request):
    all_messages = Message.objects.all().order_by("-date")
    return render(request, "messages.html", {"messages": all_messages})


@login_required(login_url="login")
def mark_read(request, id):
    msg = get_object_or_404(Message, id=id)
    msg.read = True
    msg.save()
    return redirect("messages")


# ==================================================================
# Attendance
# ==================================================================

@login_required(login_url="login")
def attendance_pdf(request):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="attendance.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Attendance Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    data = [["Student", "Roll No", "Class", "Date", "Status"]]
    records = Attendance.objects.select_related("student").order_by("-date")

    if records.exists():
        for att in records:
            data.append([
                att.student.name,
                att.student.roll_no,
                att.student.class_name,
                att.date.strftime("%Y-%m-%d"),
                att.status,
            ])
    else:
        data.append(["No records found", "", "", "", ""])

    table = Table(data, colWidths=[120, 60, 60, 80, 80])
    table.setStyle(PDF_TABLE_STYLE)
    elements.append(table)
    doc.build(elements)
    return response


# ==================================================================
# Funds
# ==================================================================

@login_required(login_url="login")
def funds_list(request):
    funds = Fund.objects.all()
    total_income = Fund.objects.filter(fund_type="Income").aggregate(Sum("amount"))["amount__sum"] or 0
    total_expenditure = Fund.objects.filter(fund_type="Expenditure").aggregate(Sum("amount"))["amount__sum"] or 0
    balance = total_income - total_expenditure

    context = {
        "funds": funds,
        "total_income": total_income,
        "total_expenditure": total_expenditure,
        "balance": balance,
    }
    return render(request, "funds.html", context)


@login_required(login_url="login")
def add_fund(request):
    if request.method == "POST":
        Fund.objects.create(
            title=request.POST.get("title"),
            amount=request.POST.get("amount"),
            fund_type=request.POST.get("fund_type"),
            description=request.POST.get("description"),
        )
        return redirect("funds")
    return render(request, "add_fund.html")


@login_required(login_url="login")
def edit_fund(request, id):
    fund = get_object_or_404(Fund, id=id)
    if request.method == "POST":
        fund.title = request.POST.get("title")
        fund.amount = request.POST.get("amount")
        fund.fund_type = request.POST.get("fund_type")
        fund.description = request.POST.get("description")
        fund.save()
        return redirect("funds")
    return render(request, "edit_fund.html", {"fund": fund})


@login_required(login_url="login")
def delete_fund(request, id):
    fund = get_object_or_404(Fund, id=id)
    if request.method == "POST":
        fund.delete()
        return redirect("funds")
    return render(request, "delete_fund.html", {"fund": fund})


# ==================================================================
# Fee Voucher (select -> preview -> download)
# ==================================================================

@login_required(login_url="login")
def select_student_fee(request):
    students = Student.objects.all()
    return render(request, "select_student_fee.html", {"students": students})


@login_required(login_url="login")
def generate_fee_voucher(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    fees = Fee.objects.filter(student=student)
    context = {"student": student, "fees": fees}

    if request.GET.get("download") == "pdf":
        template = get_template("fee_voucher.html")
        html = template.render(context)
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="fee_voucher_{student.id}.pdf"'
        pisa.CreatePDF(html, dest=response)
        return response

    return render(request, "fee_voucher.html", context)


# ==================================================================
# Teacher Salary Slip (select -> preview -> download)
# ==================================================================

@login_required(login_url="login")
def select_teacher_salary(request):
    teachers = Teacher.objects.all()
    return render(request, "select_teacher_salary.html", {"teachers": teachers})


@login_required(login_url="login")
def generate_salary_slip(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    context = {"teacher": teacher, "today": datetime.date.today()}

    if request.GET.get("download") == "pdf":
        template = get_template("salary_slip.html")
        html = template.render(context)
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="salary_slip_{teacher.id}.pdf"'
        pisa.CreatePDF(html, dest=response)
        return response

    return render(request, "salary_slip.html", context)


# ==================================================================
# Staff Salary Slip (select -> preview -> download)
# ==================================================================

@login_required(login_url="login")
def select_staff_salary(request):
    staff_list = Staff.objects.all()
    return render(request, "select_staff_salary.html", {"staff_list": staff_list})


@login_required(login_url="login")
def generate_staff_salary_slip(request, staff_id):
    staff = get_object_or_404(Staff, id=staff_id)
    context = {"staff": staff, "today": datetime.date.today()}

    if request.GET.get("download") == "pdf":
        template = get_template("staff_salary_slip.html")
        html = template.render(context)
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="staff_salary_slip_{staff.id}.pdf"'
        pisa.CreatePDF(html, dest=response)
        return response

    return render(request, "staff_salary_slip.html", context)


# ==================================================================
# Result Card (select -> preview -> download)
# ==================================================================

@login_required(login_url="login")
def select_student_result(request):
    students = Student.objects.all()
    return render(request, "select_student_result.html", {"students": students})


@login_required(login_url="login")
def generate_result_card(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    results = Result.objects.filter(student=student)

    total_obtained = sum(r.marks_obtained for r in results)
    total_marks = sum(r.total_marks for r in results)
    percentage = (total_obtained / total_marks) * 100 if total_marks > 0 else 0

    context = {
        "student": student,
        "results": results,
        "total_obtained": total_obtained,
        "total_marks": total_marks,
        "percentage": round(percentage, 2),
    }

    if request.GET.get("download") == "pdf":
        template = get_template("result_card.html")
        html = template.render(context)
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="result_card_{student.id}.pdf"'
        pisa.CreatePDF(html, dest=response)
        return response

    return render(request, "result_card.html", context)


# ==================================================================
# Raw PDF downloads (used by the "Download PDF" buttons on the
# result card / salary slip preview pages)
# ==================================================================

@login_required(login_url="login")
def download_result_card(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    results = Result.objects.filter(student=student)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="result_card_{student.name}.pdf"'

    p_canvas = _build_result_card_pdf(response, student, results)
    return response


def _build_result_card_pdf(response, student, results):
    from reportlab.pdfgen import canvas

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2, height - 50, "School Result Card")

    p.setFont("Helvetica", 12)
    p.drawString(50, height - 90, f"Name: {student.name}")
    p.drawString(50, height - 110, f"Class: {student.class_name}")
    p.drawString(50, height - 130, f"Roll No: {student.roll_no}")

    y = height - 170
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Subject")
    p.drawString(250, y, "Marks Obtained")
    p.drawString(400, y, "Total Marks")
    y -= 20

    p.setFont("Helvetica", 12)
    for r in results:
        p.drawString(50, y, r.subject)
        p.drawString(250, y, str(r.marks_obtained))
        p.drawString(400, y, str(r.total_marks))
        y -= 20

    p.setFont("Helvetica-Oblique", 10)
    p.drawCentredString(
        width / 2, 50,
        "Education is the most powerful weapon which you can use to change the world.",
    )

    p.showPage()
    p.save()
    return p


@login_required(login_url="login")
def download_salary_slip(request, teacher_id):
    teacher = get_object_or_404(Teacher, pk=teacher_id)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="salary_slip_{teacher.name}.pdf"'

    from reportlab.pdfgen import canvas

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2, height - 50, "School Salary Slip")

    p.setFont("Helvetica", 12)
    p.drawString(50, height - 100, f"Name: {teacher.name}")
    p.drawString(50, height - 120, f"Subject: {teacher.subject}")

    y = height - 170
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Basic Salary:")
    p.drawString(250, y, str(teacher.basic_salary))
    y -= 20

    p.drawString(50, y, "Allowances:")
    p.drawString(250, y, str(teacher.allowances))
    y -= 20

    p.drawString(50, y, "Deductions:")
    p.drawString(250, y, str(teacher.deductions))
    y -= 40

    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Net Salary:")
    p.drawString(250, y, str(teacher.net_salary()))

    p.setFont("Helvetica-Oblique", 10)
    p.drawCentredString(width / 2, 50, "This is a system-generated salary slip. No signature required.")

    p.showPage()
    p.save()
    return response


# ==================================================================
# Edit result / salary (used from result card & salary slip pages)
# ==================================================================

@login_required(login_url="login")
def edit_result(request, pk):
    result = get_object_or_404(Result, pk=pk)
    if request.method == "POST":
        form = ResultForm(request.POST, instance=result)
        if form.is_valid():
            form.save()
            return redirect("generate_result_card", student_id=result.student_id)
    else:
        form = ResultForm(instance=result)
    return render(request, "edit_result.html", {"form": form})


@login_required(login_url="login")
def edit_salary(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    if request.method == "POST":
        form = SalaryForm(request.POST, instance=teacher)
        if form.is_valid():
            form.save()
            return redirect("generate_salary_slip", teacher_id=teacher.pk)
    else:
        form = SalaryForm(instance=teacher)
    return render(request, "edit_salary.html", {"form": form})
