from odoo import http
from odoo.http import request
from ..utils.fcm import send_push
try:
    from firebase_admin import messaging
except ImportError:
    messaging = None
import json


class RegisterFCMTokenAPI(http.Controller):

    # =====================================================
    # ✅ POST REGISTER TOKEN - From mobile app
    # =====================================================

    @http.route(
        '/api/push/register',
        type='http',
        auth='user',
        methods=['POST'],
        csrf=False
    )
    def register_device_post(self, **kwargs):

        import json
        data = json.loads(request.httprequest.data or '{}')

        fcm_token = data.get('fcm_token')
        platform = data.get('platform')

        if not fcm_token or not platform:
            return request.make_response(
                json.dumps({
                    "status": "error",
                    "message": "fcm_token and platform are required"
                }),
                headers=[('Content-Type', 'application/json')]
            )

        Device = request.env['push.device'].sudo()

        # Remove token if previously registered under another user on this device
        stale_devices = Device.search([
            ('fcm_token', '=', fcm_token),
            ('user_id', '!=', request.env.user.id)
        ])
        if stale_devices:
            stale_devices.unlink()

        # Remove old device tokens for the current user (keeps only 1 active token per user)
        old_user_devices = Device.search([
            ('user_id', '=', request.env.user.id),
            ('fcm_token', '!=', fcm_token)
        ])
        if old_user_devices:
            old_user_devices.unlink()

        # Check if already registered for current user
        device = Device.search([
            ('user_id', '=', request.env.user.id),
            ('fcm_token', '=', fcm_token)
        ], limit=1)

        if device:
            device.write({
                'platform': platform,
                'active': True
            })
            action = "updated"
        else:
            Device.create({
                'user_id': request.env.user.id,
                'fcm_token': fcm_token,
                'platform': platform,
                'active': True
            })
            action = "created"

        return request.make_response(
            json.dumps({
                "status": "ok",
                "action": action,
                "message": f"FCM token {action} successfully"
            }),
            headers=[('Content-Type', 'application/json')]
        )
    

    # =====================================================
    # ✅ SEND USER NOTIFICATION - From odoo
    # =====================================================

    @http.route(
        '/api/push/send/users',
        type='json',
        auth='user',
        methods=['POST'],
        csrf=False
    )
    def send_push_to_users(self, **kwargs):
        # data = request.jsonrequest
        data = json.loads(request.httprequest.data or '{}')

        if not data.get('user_ids') or not data.get('title') or not data.get('body'):
            return {"status": "error", "message": "Missing required fields"}

        return request.env['push.service'].sudo().send_to_users(
            user_ids=data['user_ids'],
            title=data['title'],
            body=data['body']
        )
