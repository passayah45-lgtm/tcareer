import json
from rest_framework.renderers import JSONRenderer


class StandardRenderer(JSONRenderer):
    """
    Wraps every API response in a consistent envelope:

    Success:
        { "success": true, "data": {...}, "errors": {}, "meta": {} }

    Error:
        { "success": false, "data": null, "errors": {...}, "meta": {} }

    This means frontend developers never have to guess the response shape.
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        renderer_context = renderer_context or {}
        response = renderer_context.get("response")
        status_code = response.status_code if response else 200
        success = status_code < 400

        if (
            isinstance(data, dict)
            and {"success", "data", "errors", "meta"}.issubset(data.keys())
        ):
            return json.dumps(data, cls=self.encoder_class).encode()

        if not success:
            envelope = {
                "success": False,
                "data": None,
                "errors": data if isinstance(data, dict) else {"detail": data},
                "meta": {},
            }
        else:
            meta = renderer_context.get("meta", {})
            # Support pagination meta passed via response
            if hasattr(response, "data") and isinstance(data, dict):
                if "count" in data and "results" in data:
                    meta = {
                        "count": data.get("count"),
                        "next": data.get("next"),
                        "previous": data.get("previous"),
                    }
                    data = data.get("results")

            envelope = {
                "success": True,
                "data": data,
                "errors": {},
                "meta": meta,
            }

        return json.dumps(envelope, cls=self.encoder_class).encode()
