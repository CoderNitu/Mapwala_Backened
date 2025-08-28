from rest_framework.renderers import JSONRenderer
from rest_framework.utils import json


class CustomJSONRenderer(JSONRenderer):
    charset = 'utf-8'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response", None)
        request = renderer_context.get("request", None)

        # Pick msg from view/response if present
        msg = None
        if isinstance(data, dict) and "msg" in data:
            msg = data.pop("msg")  # remove msg from data payload

        # Default structure
        response_dict = {
            "success": True,
            "status": response.status_code if response else 200,
            "msg": msg or "Request processed successfully",
            "data": data,
        }

        # Handle errors
        if response is not None and response.status_code >= 400:
            response_dict["success"] = False
            response_dict["msg"] = "Something went wrong"
            response_dict["errors"] = data
            response_dict["data"] = None

        return json.dumps(response_dict)
