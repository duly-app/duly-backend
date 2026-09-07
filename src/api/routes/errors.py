from flask import jsonify, request


def page_not_found(error: Exception):
    if request.accept_mimetypes.accept_json:
        return jsonify({"message": "Page not found"}), 404

    return "Page not found", 404


def internal_server_error(error: Exception):
    if request.accept_mimetypes.accept_json:
        return jsonify({"message": "Internal server error"}), 500

    return "Internal server error", 500
