from flask import session
from datetime import timezone
       
#handles type casting        
def start_password_reset(user, code):
    session["is_resetting_password"] = True
    session["user_id"] = int(user.id)
    session["current_email"] = str(user.email)
    session["verification_code_id"] = int(code.id)


def clear_password_reset():
    for key in (
        "is_resetting_password",
        "user_id",
        "current_email",
        "verification_code_id",
    ):
        session.pop(key, None)

def ensure_utc(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt