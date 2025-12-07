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

# Пример теста
if __name__ == "__main__":
    send_notification("demchenko.nina2004@gmail.com", "Привет", "email")
    send_notification("+71234567890", "Привет", "sms")