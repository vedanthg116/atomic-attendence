import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_notification(student_name, status, parent_email):
    sender_email = "gamerapprovedd98@gmail.com"  # Update with your email address
    sender_password = "Marsinspace@99"  # Update with your email password
    subject = "Student Attendance Notification"
    body = (f"Dear Parent,\n\nThis is to inform you that your child, {student_name}, was {status} in class "
            f"today.\n\nBest regards,\nYour School")

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = parent_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, parent_email, msg.as_string())
        return True
    except Exception as e:
        print("Email sending failed:", str(e))
        return False

# Modify parent_email_dict to use student's information as keys
parent_email_dict = {
    "21BTRCL000_PL": "21btrcl079@jainuniversity.ac.in",
}
