import re

USERID = "currentUserId"
TOKEN = "currentToken"
PROFILEID = "currentProfileId"

USERNAME_PATTERN = r"^[a-zA-Z0-9_.-]{3,30}$"
USERNAME_REGEX = re.compile(USERNAME_PATTERN)
