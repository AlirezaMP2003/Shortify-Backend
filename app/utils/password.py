import re


MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128


def validate_password(password: str) -> str | None:
    if len(password) < MIN_PASSWORD_LENGTH:
        return "رمز عبور باید حداقل ۸ کاراکتر باشد."

    if len(password) > MAX_PASSWORD_LENGTH:
        return "رمز عبور نمی‌تواند بیشتر از ۱۲۸ کاراکتر باشد."

    if re.search(r"\s", password):
        return "رمز عبور نباید شامل فاصله یا کاراکترهای خالی باشد."

    if not re.search(r"[A-Z]", password):
        return "رمز عبور باید حداقل شامل یک حرف بزرگ انگلیسی باشد."

    if not re.search(r"[a-z]", password):
        return "رمز عبور باید حداقل شامل یک حرف کوچک انگلیسی باشد."

    if not re.search(r"\d", password):
        return "رمز عبور باید حداقل شامل یک عدد باشد."

    if not re.search(r"[^A-Za-z0-9]", password):
        return "رمز عبور باید حداقل شامل یک کاراکتر ویژه باشد."

    return None