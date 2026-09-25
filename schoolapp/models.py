import datetime
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User


class Student(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="students")
  # 👈 new
    name = models.CharField(max_length=100)
    roll_no = models.CharField(max_length=20)
    class_name = models.CharField(max_length=50)
    email = models.EmailField()
    father_name = models.CharField(max_length=100, blank=True, null=True)   # 👈 added
    contact = models.CharField(max_length=20, blank=True, null=True) 

    def __str__(self):
        return f"{self.name} ({self.class_name})"


class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField(default=datetime.date.today)   # ✅ today’s date
    status = models.CharField(max_length=10, choices=[('Present', 'Present'), ('Absent', 'Absent')])

    def __str__(self):
        return f"{self.student.name} - {self.date} - {self.status}"


class Teacher(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="teachers")
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=50)
    email = models.EmailField()
    
    # Salary fields
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def net_salary(self):
        return self.basic_salary + self.allowances - self.deductions

    def __str__(self):
        return self.name

class Lecture(models.Model): 
    DAY_CHOICES = [("Monday","Monday"),("Tuesday","Tuesday"),("Wednesday","Wednesday"),("Thursday","Thursday"),("Friday","Friday"),("Saturday","Saturday")]
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="lectures")
    subject = models.CharField(max_length=50)
    class_name = models.CharField(max_length=20)
    day_of_week = models.CharField(max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=30, blank=True)

    class Meta:
        ordering = ["day_of_week", "start_time"]

    def __str__(self):
        return f"{self.subject} - {self.class_name} ({self.day_of_week} {self.start_time.strftime('%H:%M')})"


class Staff(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name="staff")
    name = models.CharField(max_length=100)
    designation = models.CharField(max_length=50)
    employee_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    contact = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Notice(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_date = models.DateField()

    def __str__(self):
        return self.title


class Fee(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=[("Paid", "Paid"), ("Pending", "Pending")])
    date = models.DateField(default=timezone.now)   

    def __str__(self):
        return f"{self.student.name} - {self.status}"


class Message(models.Model):
    sender = models.CharField(max_length=100)
    content = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"From: {self.sender} - {'Read' if self.read else 'Unread'}"
    
    

class Fund(models.Model):
    FUND_TYPES = [
        ("Income", "Income"),
        ("Expenditure", "Expenditure"),
    ]

    title = models.CharField(max_length=200)   # Short description
    fund_type = models.CharField(
        max_length=20,
        choices=FUND_TYPES,
        default="Income"   # ✅ Default prevents migration errors
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Enter amount in PKR"
    )
    date = models.DateField(auto_now_add=True)  # Auto sets the date when added
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-date"]  # ✅ Show latest transactions first

    def __str__(self):
        return f"{self.title} - {self.fund_type} ({self.amount})"


class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    marks_obtained = models.IntegerField(default=0)
    total_marks = models.IntegerField(default=100)
    grade = models.CharField(max_length=5, blank=True, null=True)

    def __str__(self):
        return f"{self.student.name} - {self.subject}"


