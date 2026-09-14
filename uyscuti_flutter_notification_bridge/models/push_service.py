from odoo import models
try:
    from firebase_admin import messaging
except ImportError:
    messaging = None
from ..utils.fcm import send_push


class PushService(models.AbstractModel):
    _name = 'push.service'
    _description = 'Push Notification Service'

    # -------------------------
    # SINGLE USER
    # -------------------------
    def send_to_user(self, user_id, title, body, data=None):
        Device = self.env['push.device'].sudo()
        devices = Device.search([('user_id', '=', user_id), ('active', '=', True)])

        if not devices:
            return {"status": "no_device"}

        success_count = 0
        failed_count = 0
        errors = []

        payload_data = data.copy() if data else {}
        if "user_id" not in payload_data:
            payload_data["user_id"] = str(user_id)

        for device in devices:
            try:
                send_push(
                    self.env,
                    device.fcm_token,
                    title,
                    body,
                    payload_data
                )
                success_count += 1
            except messaging.UnregisteredError:
                device.unlink()
            except Exception as e:
                failed_count += 1
                errors.append(str(e))

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


# Action User

# self.env['push.service'].send_to_users(
#     user_ids=[1, 3, 7],
#     title="System Update",
#     body="Maintenance tonight"
# )

# self.env['push.service'].send_to_user(
#     user_id=self.user_id.id,
#     title="Order Confirmed",
#     body="Your order has been confirmed"
# )
