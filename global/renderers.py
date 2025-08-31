from rest_framework.renderers import JSONRenderer

class CustomRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response", None)

        if response is not None and 200 <= response.status_code < 300:
            # If view already sent success + message
            if isinstance(data, dict) and "success" in data and "message" in data:
                final_data = {
                    "success": data.get("success", True),
                    "status": response.status_code,
                    "msg": data.get("message", "Request processed successfully"),
                    "data": data.get("data", None),  # only actual payload
                }
                # keep extra keys like 'count' if they exist
                for key in ["count", "error", "errors"]:
                    if key in data:
                        final_data[key] = data[key]
                data = final_data
            else:
                # fallback: generic success wrapper
                data = {
                    "success": True,
                    "status": response.status_code,
                    "msg": "Request processed successfully",
                    "data": data,
                }

        return super().render(data, accepted_media_type, renderer_context)

