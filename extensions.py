import os
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

csrf = CSRFProtect()
limiter = Limiter(
    get_remote_address,
    default_limits=["3000 per day", "500 per hour"],
    storage_uri=os.environ.get("REDIS_URL", "memory://"),
)
