import smtplib
from email.message import EmailMessage

def send_email(subject, body, to_email, from_email, smtp_server, smtp_port, login, password):
    # Create the email message
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    msg.set_content(body)

    # Connect to the SMTP server and send the email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()  # Upgrade the connection to secure (TLS)
        server.login(login, password)
        server.send_message(msg)
        print("Email sent successfully!")

# Example usage
send_email(
    subject="Test Email",
    body="This is a test email sent using Python!",
    to_email="vedabezaleel@gmail.com",
    from_email="raiharc@gmail.com",
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    login="raiharc@gmail.com",
    password="fmaf ulzb syvw zvgd"
)
