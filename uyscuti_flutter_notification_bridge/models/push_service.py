import json
import logging
from odoo import models
try:
    from firebase_admin import messaging
except ImportError:
    messaging = None
from ..utils.fcm import send_push

_logger = logging.getLogger(__name__)


class PushService(models.AbstractModel):
    _name = 'push.service'
    _description = 'Push Notification Service'

    # -------------------------
    # SINGLE USER
    # -------------------------
    def send_to_user(self, user_id, title, body, data=None):
        Device = self.env['push.device'].sudo()
        PushLog = self.env['push.log'].sudo()
        devices = Device.search([('user_id', '=', user_id), ('active', '=', True)])

        if not devices:
            # Log failed attempt due to no active device
            try:
                PushLog.create({
                    'user_id': user_id,
                    'title': title,
                    'body': body,
                    'status': 'failed',
                    'error_message': 'No registered active device for user.',
                    'data_payload': json.dumps(data) if data else '',
                })
            except Exception as e:
                _logger.warning("Could not create push log: %s", e)
            return {"status": "no_device"}

        success_count = 0
        failed_count = 0
        errors = []

        payload_data = data.copy() if data else {}
        if "user_id" not in payload_data:
            payload_data["user_id"] = str(user_id)

        for device in devices:
            try:
                msg_id = send_push(
                    self.env,
                    device.fcm_token,
                    title,
                    body,
                    payload_data
                )
                success_count += 1
                try:
                    PushLog.create({
                        'user_id': user_id,
                        'device_id': device.id,
                        'title': title,
                        'body': body,
                        'status': 'success',
                        'message_id': str(msg_id) if msg_id else '',
                        'data_payload': json.dumps(payload_data) if payload_data else '',
                    })
                except Exception as log_err:
                    _logger.warning("Could not create push log: %s", log_err)

            except messaging.UnregisteredError if messaging else Exception:
                device.unlink()
                try:
                    PushLog.create({
                        'user_id': user_id,
                        'device_id': device.id,
                        'title': title,
                        'body': body,
                        'status': 'failed',
                        'error_message': 'Unregistered/Invalid FCM token. Device unlinked.',
                        'data_payload': json.dumps(payload_data) if payload_data else '',
                    })
                except Exception as log_err:
                    _logger.warning("Could not create push log: %s", log_err)

            except Exception as e:
                failed_count += 1
                errors.append(str(e))
                try:
                    PushLog.create({
                        'user_id': user_id,
                        'device_id': device.id,
                        'title': title,
                        'body': body,
                        'status': 'failed',
                        'error_message': str(e),
                        'data_payload': json.dumps(payload_data) if payload_data else '',
                    })
                except Exception as log_err:
                    _logger.warning("Could not create push log: %s", log_err)

        if success_count > 0:
            return {"status": "success", "sent_count": success_count}
        elif failed_count > 0:
            return {"status": "failed", "error": "; ".join(errors)}
        else:
            return {"status": "invalid_token"}

    # -------------------------
    # MULTIPLE USERS
    # -------------------------
    def send_to_users(self, user_ids, title, body, data=None):
        results = {
            "success": [],
            "failed": [],
            "invalid": []
        }

        for user_id in user_ids:
            res = self.send_to_user(user_id, title, body, data)

            if res["status"] == "success":
                results["success"].append(user_id)
            elif res["status"] == "invalid_token":
                results["invalid"].append(user_id)
            else:
                results["failed"].append({
                    "user_id": user_id,
                    "error": res.get("error")
                })

        return results
