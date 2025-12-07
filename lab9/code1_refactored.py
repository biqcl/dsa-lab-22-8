# Рефакторинг (удаление дублирования, вынесение общей логики)
def send_notification(to, message, service_type):
    if service_type == "email":
        print(f"Connecting to SMTP server...")
        print(f"Sending email to {to} with subject '{message}'...")
        print("Email sent.")
    elif service_type == "sms":
        print(f"Connecting to SMS gateway...")
        print(f"Sending SMS to {to} with message '{message}'...")
        print("SMS sent.")

if __name__ == "__main__":
    send_notification("m_byzovaa@mail.ru", "Привет", "email")
    send_notification("+78888888888", "Привет", "sms")
