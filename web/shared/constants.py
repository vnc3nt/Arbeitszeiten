import re

USERID = "currentUserId"
TOKEN = "currentToken"

USERNAME_PATTERN = "[^ ]{8,}"
USERNAME_REGEX = re.compile(USERNAME_PATTERN)

COLOR_PATTERN = "[0-9a-fA-F]{6}"
COLOR_REGEX = re.compile(COLOR_PATTERN)

# API
GET_LOCATIONS = ["args"]
POST_LOCATIONS = ["json", "form"]
DELETE_LOCATIONS = ["json", "form"]
PATCH_LOCATIONS = ["json", "form"]

AUTH_TYPE_REGISTER = "register"
AUTH_TYPE_LOGIN = "login"
AUTH_TYPE_LOGOUT = "logout"


# G Cache
G_USER = "user_cache"
