import json
import os

import ee

PROJECT_ID = os.environ.get("EE_PROJECT_ID", "studied-market-509102-a7")

_initialised = False

def init_earth_engine():
    """
    Deployed:  EE_SERVICE_ACCOUNT_KEY holds the service-account JSON key.
    Cloud Run: the attached service account is used.
    Local dev: falls back to your own `ee.Authenticate()` login.
    Safe to call more than once.
    """

    global _initialised
    if _initialised:
        return

    key_json = os.environ.get("EE_SERVICE_ACCOUNT_KEY")

    if key_json:
        email = json.loads(key_json)["client_email"]
        credentials = ee.ServiceAccountCredentials(email, key_data=key_json)
        ee.Initialize(credentials, project=PROJECT_ID)

    else:
        try:
            import google.auth
            credentials, _ = google.auth.default(scopes=[
                "https://www.googleapis.com/auth/earthengine",
                "https://www.googleapis.com/auth/cloud-platform",
            ])
            ee.Initialize(credentials, project=PROJECT_ID)
        except Exception:
            ee.Initialize(project=PROJECT_ID)

    _initialised = True