from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        errors = response.data

        # Flatten errors: remove field names, just take the messages
        flattened = []
        if isinstance(errors, dict):
            for key, value in errors.items():
                if isinstance(value, list):
                    flattened.extend(value)
                else:
                    flattened.append(value)
        elif isinstance(errors, list):
            flattened.extend(errors)
        else:
            flattened.append(str(errors))

        # If only one error message, return it directly instead of a list
        if len(flattened) == 1:
            flattened = flattened[0]

        response.data = {
            "success": False,
            "status": response.status_code,
            "errors": flattened
        }

    return response
