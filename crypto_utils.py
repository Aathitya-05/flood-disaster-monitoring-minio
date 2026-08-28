"""
Application-level object encryption (AES-256-GCM).

MinIO's own server-side encryption requires a full external Key
Management Service (Vault / AWS KMS / MinIO KES) in current releases -
verified empirically: setting MINIO_KMS_SECRET_KEY alone does nothing
in this MinIO version, the object body is stored as plain bytes on
disk regardless. Standing up a separate KES server is a large, fragile
addition for a self-contained deployment, so encryption is done here
instead, at the application layer, before bytes ever reach MinIO.

Every object body (image/video/CSV/JSON bytes) is encrypted client-side
with AES-256-GCM before upload and decrypted after download. Object
metadata (district, flood-level, timestamps, etc.) stays in plaintext
so bucket browsing and metadata-based filtering keep working without
decrypting every object first - this matches how real S3 server-side
encryption also only covers the object body, never its metadata.
"""

import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Demo default key - override via the OBJECT_ENC_KEY env var (local
# scripts) or the OBJECT_ENC_KEY Streamlit secret (deployed app) for a
# real deployment. Rotating the key requires re-encrypting existing
# objects (re-run the upload pipeline) since old ones stay encrypted
# under whatever key was active when they were written.
_DEFAULT_KEY_B64 = "49rvqM8tzDXxgUbwA5YFPxi5rKx4lNvmnGV5PcjK/EU="

_NONCE_SIZE = 12  # 96-bit nonce, standard for AES-GCM


def get_encryption_key():
    """Returns the raw 32-byte AES key. Checks the OBJECT_ENC_KEY env var
    first (base64-encoded), falling back to the built-in demo default."""
    key_b64 = os.environ.get("OBJECT_ENC_KEY", _DEFAULT_KEY_B64)
    return base64.b64decode(key_b64)


def encrypt_bytes(plaintext: bytes, key: bytes = None) -> bytes:
    """Encrypts plaintext with AES-256-GCM. Returns nonce || ciphertext_with_tag."""
    key = key or get_encryption_key()
    nonce = os.urandom(_NONCE_SIZE)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
    return nonce + ciphertext


def decrypt_bytes(blob: bytes, key: bytes = None) -> bytes:
    """Reverses encrypt_bytes(). Raises if the key is wrong or the data
    was tampered with (GCM authentication tag verification fails)."""
    key = key or get_encryption_key()
    nonce, ciphertext = blob[:_NONCE_SIZE], blob[_NONCE_SIZE:]
    return AESGCM(key).decrypt(nonce, ciphertext, None)
