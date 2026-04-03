import re

# G and session cache
SESSION_USER_TOKEN = "currentToken"
SESSION_FORM_DATA = "form-data"
G_USER = "user"
G_CURRENT_PROFILE = "cur_profile"

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

# App behaviour
DEFAULT_CATEGORIES = [("Work", "ff6961"), ("Vacation", "A4D8D8")]  # needs to contain at least 1 element

# query params
ARGS_DATE = "date"

# form names
FORM_USERNAME = "username"
FORM_PASSWORD = "password"
FORM_CONFIRM_PASSWORD = "confirm-password"

FORM_PROFILE_ID = "profile-id"
FORM_PROFILE_NAME = "profile-name"
FORM_PROFILE_COLOR = "profile-color"
FORM_WORK_START = "work-start"
FORM_WORK_FORMAT = "work-format"
FORM_WORK_TIME = "work-time"

FORM_WORK_CATEGROY = "work-category"
FORM_WORK_BEGIN = "work-begin"
FORM_WORK_END = "work-end"
FORM_WORK_NOTE = "work-note"

# flash categories
FLASH_ERROR = "error"

