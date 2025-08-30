
from rest_framework.renderers import JSONRenderer

class CustomRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response", None)

        # Only shape success responses here, not errors (errors handled separately)
        if response is not None and 200 <= response.status_code < 300:
            data = {
                "success": True,
                "status": response.status_code,
                "msg": "Request processed successfully",
                "data": data,
            }
        return super().render(data, accepted_media_type, renderer_context)
