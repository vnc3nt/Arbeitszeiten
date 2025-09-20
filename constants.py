import re

USERID = "currentUserId"
TOKEN = "currentToken"

USERNAME_PATTERN = "[^ ]{8,}"
USERNAME_REGEX = re.compile(USERNAME_PATTERN)
