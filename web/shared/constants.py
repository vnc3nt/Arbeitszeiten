import re

# G cache
G_USER_TOKEN = "currentToken"
G_USER = "user"

# Patterns
USERNAME_PATTERN = "[^ ]{8,}"
USERNAME_REGEX = re.compile(USERNAME_PATTERN)

COLOR_PATTERN = "[0-9a-fA-F]{6}"
COLOR_REGEX = re.compile(COLOR_PATTERN)

# API
GET_LOCATIONS = ["args"]
POST_LOCATIONS = ["json", "form"]
DELETE_LOCATIONS = ["json", "form"]
PATCH_LOCATIONS = ["json", "form"]
PUT_LOCATIONS = ["json", "form"]

AUTH_TYPE_REGISTER = "register"
AUTH_TYPE_LOGIN = "login"
AUTH_TYPE_LOGOUT = "logout"

HEADER_LOGIN_TOKEN = "Authorization"

API_DATE_FORMAT = "%Y-%m-%d"
API_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S:%f"

# database
CONSTRAINT_UNIQUE_PROFILE_CATEGORY = "UniqueProfileCategory"
CONSTRAINT_UNIQUE_PROFILE_WORK_PERIOD = "UniqueProfileWorkPeriod"
CONSTRAINT_UNIQUE_PROFILE_NAME = "UniqueProfileName"

# G Cache
G_USER = "user_cache"

# App behaviour
DEFAULT_CATEGORIES = [("Work", "ff6961"), ("Vacation", "A4D8D8")]  # needs to contain at least 1 element

# flash categories
FLASH_ERROR = "error"