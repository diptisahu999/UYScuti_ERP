import json
import logging

_logger = logging.getLogger(__name__)

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
except ImportError:
    firebase_admin = None
    credentials = None
    messaging = None
    _logger.warning("firebase_admin library not installed. Please install with 'pip install firebase-admin'")


def get_firebase_app(env):
    if not firebase_admin:
        raise ImportError("firebase_admin library is not installed. Run 'pip install firebase-admin'")

    # ✅ Prevent multiple initialization
    if firebase_admin._apps:
        return firebase_admin.get_app()

    # ✅ Get JSON from Odoo DB - Settings → Technical → System Parameters - firebase.service.account
    param = env['ir.config_parameter'].sudo().get_param('firebase.service.account')

    if not param:
        raise ValueError("Firebase config not found in system parameters")

    config = json.loads(param)
    cred = credentials.Certificate(config)

    return firebase_admin.initialize_app(cred)


def send_push(env, token, title, body, data=None):
    if not firebase_admin:
        _logger.warning("Cannot send push notification: firebase_admin is not installed.")
        return None

    app = get_firebase_app(env)

    # Ensure all data values are strings for FCM compatibility
    formatted_data = {}
    if data:
        for k, v in data.items():
            formatted_data[str(k)] = str(v) if v is not None else ""

    # Android specific configuration
    android_config = messaging.AndroidConfig(
        priority='high',
        notification=messaging.AndroidNotification(
            title=title,
            body=body,
            sound='default',
            channel_id='high_importance_channel',
            default_sound=True,
            default_vibrate_timings=True,
        )
    )

    # iOS / APNs specific configuration
    apns_config = messaging.APNSConfig(
        headers={'apns-priority': '10'},
        payload=messaging.APNSPayload(
            aps=messaging.Aps(
                alert=messaging.ApsAlert(
                    title=title,
                    body=body,
                ),
                sound='default',
                badge=1,
                content_available=True,
            )
        )
    )

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=formatted_data,
        token=token,
        android=android_config,
        apns=apns_config,
    )

    return messaging.send(message, app=app)