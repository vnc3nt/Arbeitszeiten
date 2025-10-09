import re

USERID = "currentUserId"
TOKEN = "currentToken"

USERNAME_PATTERN = "[^ ]{8,}"
USERNAME_REGEX = re.compile(USERNAME_PATTERN)

# API
GET_LOCATIONS = ["args"]
POST_LOCATIONS = ["json", "form"]
DELETE_LOCATIONS = ["json", "form"]
PATCH_LOCATIONS = ["json", "form"]

AUTH_TYPE_REGISTER = "register"
AUTH_TYPE_LOGIN = "login"


# G Cache
G_USER = "user_cache"
