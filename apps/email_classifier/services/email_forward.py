from django.core.mail import EmailMultiAlternatives
from email_classifier.models import DepartmentMail

def forward_email(original_from: str, original_subject: str, original_body: str, department: str):
    department_map = {
        dept_mail.department.name: dept_mail.mail
        for dept_mail in DepartmentMail.objects.select_related("department").all()
    }
    recipient_email = department_map.get(department)

    if not recipient_email:
        raise Exception(f"Department '{department}' not found in DepartmentMail")

    # Email subject
    subject = f"[Forwarded to {department}] {original_subject}"

    # Plain text version
    text_content = f"""
    This email was automatically forwarded to the {department} department.

    ----- Original Message -----
    From: {original_from}
    Subject: {original_subject}

    {original_body}
    """

    # Optional HTML version (for better formatting)
    html_content = f"""
    <p>This email was automatically forwarded to the <strong>{department}</strong> department.</p>
    <hr>
    <p><strong>From:</strong> {original_from}<br>
    <strong>Subject:</strong> {original_subject}</p>
    <pre style="font-family: monospace">{original_body}</pre>
    """

    try:
        msg = EmailMultiAlternatives(subject, text_content, from_email=None, to=[recipient_email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        print(f"[✓] Email forwarded to {department} ({recipient_email})")
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")

