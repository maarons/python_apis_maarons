from base64 import urlsafe_b64decode
import json
import hashlib
import hmac
from time import time

class LoginException(Exception):
    pass

def cherrypy_authenticate(fb_app_id, fb_app_secret):
    import cherrypy
    cherrypy.request.fb_user_id = None
    name = "fbsr_" + fb_app_id
    if name not in cherrypy.request.cookie:
        raise LoginException("Cookie not present")
    signed_request = cherrypy.request.cookie[name].value
    fb_user_id = authenticate(signed_request, fb_app_secret)
    cherrypy.request.fb_user_id = fb_user_id

def authenticate(signed_request, fb_app_secret):
        sig_and_payload = signed_request.split(".", 1)
        if len(sig_and_payload) != 2:
            raise LoginException("Expected signature and payload")
        (encoded_sig, payload, ) = sig_and_payload
        # Python requires base64 padding and useless convertions between
        # str and bytes.
        def b64padding(s):
            n = len(s) % 4
            if n == 0:
                return s
            else:
                return s + "=" * (4 - n)
        try:
            sig = urlsafe_b64decode(b64padding(encoded_sig).encode("ascii"))
        except Exception as e:
            raise LoginException("Failed to decode signature", e)
        try:
            data = json.loads(urlsafe_b64decode(
                b64padding(payload).encode("ascii")
            ).decode("utf-8"))
        except Exception as e:
            raise LoginException("Failed to decode payload", e)

        expected_sig = hmac.new(
            fb_app_secret.encode("ascii"),
            payload.encode("ascii"),
            hashlib.sha256,
        ).digest()

        if sig != expected_sig:
            raise LoginException("Bad paylod signature")

        if data["issued_at"] < time() - 3600 * 24:
            raise LoginException("Request is too old")

        return int(data["user_id"])
