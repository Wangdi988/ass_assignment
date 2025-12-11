from typing import Dict, Any
import json
from datetime import datetime, timezone
import secrets

def prepare_signature_body_for_logo_upload(
    product_code: str,
    created_by: str,
    request_id: str,
    source_app: str,
    user_id: str,
    user_name: str
) -> Dict[str, str]:
    """
    Prepare request body for logo upload signature generation.
    Fields are sorted alphabetically for consistency.
    
    Args:
        product_code: Product code
        created_by: Creator name
        request_id: Request ID
        source_app: Source application identifier
        user_id: User ID
        user_name: User name
    
    Returns:
        Sorted dictionary ready for signature generation
    """
    body = {
        "created_by": created_by,
        "product_code": product_code,
        "request_id": request_id,
        "source_app": source_app,
        "user_id": user_id,
        "user_name": user_name
    }
    
    # Return sorted for consistency with signature validation
    return dict(sorted(body.items()))


def prepare_signature_payload(
    request_body: Dict[str, str],
    nonce: str = None,
    timestamp: str = None
) -> Dict[str, Any]:
    """
    Prepare complete payload for signature generation endpoint.
    
    Args:
        request_body: The request body dict (already sorted)
        nonce: Optional nonce, generates random if not provided
        timestamp: Optional timestamp, uses current UTC if not provided
    
    Returns:
        Complete payload for /api/generate/signature endpoint
    """
    if nonce is None:
        nonce = f"NONCE_{secrets.token_hex(8).upper()}"
    
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    return {
        "request_body": request_body,
        "nonce": nonce,
        "timestamp": timestamp
    }


def get_signature_string(body: Dict[str, str]) -> str:
    """
    Convert body to the exact JSON string format used in signature validation.
    
    Args:
        body: Dictionary of fields
    
    Returns:
        JSON string with consistent formatting (sorted keys, compact separators)
    """
    return json.dumps(body, sort_keys=True, separators=(",", ":"))


def extract_form_fields_for_signature(form_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract non-file fields from form data for signature validation.
    
    Args:
        form_data: Form data dictionary from request.form()
    
    Returns:
        Sorted dictionary with only text fields (no files)
    """
    signature_fields = {
        key: value
        for key, value in form_data.items()
        if not hasattr(value, "filename")  # Exclude file uploads
    }
    
    return dict(sorted(signature_fields.items()))


# Example usage constants
LOGO_UPLOAD_FIELDS = [
    "created_by",
    "product_code",
    "request_id",
    "source_app",
    "user_id",
    "user_name"
]


# app/core/digitial_sign/signature_helper.py

def extract_query_params_for_signature(query_params: Dict[str, Any], fields: list = None) -> Dict[str, str]:
    """
    Extract specific query parameters for signature validation.
    
    Args:
        query_params: Query parameters dictionary from request.query_params
        fields: List of field names to include. If None, includes all.
    
    Returns:
        Sorted dictionary with only specified fields
    """
    if fields is None:
        # Default fields for download
        fields = ["filename", "request_id", "source_app"]
    
    signature_params = {
        key: value 
        for key, value in query_params.items() 
        if key in fields
    }
    
    return dict(sorted(signature_params.items()))


def prepare_signature_body_for_logo_download(
    filename: str,
    request_id: str,
    source_app: str
) -> Dict[str, str]:
    """
    Prepare request body for logo download signature generation.
    Note: is_base64 is excluded as it's a UI preference, not a security parameter.
    
    Args:
        filename: Filename to download from S3
        request_id: Request ID for tracking
        source_app: Source application identifier
    
    Returns:
        Sorted dictionary ready for signature generation
    """
    body = {
        "filename": filename,
        "request_id": request_id,
        "source_app": source_app
    }
    
    return dict(sorted(body.items()))