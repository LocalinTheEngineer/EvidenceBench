"""Small token fixture; no external dependencies."""


def validate_token(token, now):
    if token.get("expires_at", 0) <= now:
        return False
    return bool(token.get("user"))


def issue_token(user, expires_at):
    return {"user": user, "expires_at": expires_at}
