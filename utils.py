import base64
from datetime import datetime, timezone


def datetime_now():
    return datetime.now(timezone.utc)


def base64_encode_image(image):
    return base64.b64encode(image.tobytes()).decode()