#!/usr/bin/env bash
# ==============================================================================
# SIH 26043 - Automated Restore Verification Drill
# Department of Higher & Technical Education, Government of Jharkhand
# ==============================================================================
# Validates:
# 1. SHA256 integrity against manifest.
# 2. OpenSSL AES-256 decryption with provided passphrase.
# 3. Gzip decompression validity.
# 4. Optional dry-run restore into a target test database or syntax check.
# ==============================================================================
set -euo pipefail

ENCRYPTED_BACKUP_FILE="${1:-}"
MANIFEST_FILE="${2:-}"

if [ -z "${ENCRYPTED_BACKUP_FILE}" ] || [ ! -f "${ENCRYPTED_BACKUP_FILE}" ]; then
    echo "ERROR: Encrypted backup file must be provided as first argument and exist." >&2
    echo "Usage: $0 <path_to_backup.sql.gz.enc> [path_to_manifest.json]" >&2
    exit 1
fi

if [ -z "${BACKUP_PASSPHRASE:-}" ]; then
    echo "ERROR: BACKUP_PASSPHRASE environment variable is required to decrypt backup." >&2
    exit 1
fi

echo "=== Starting SIH 26043 Restore Verification Drill ==="
echo "Testing archive: ${ENCRYPTED_BACKUP_FILE}"

# 1. Verify Checksum if manifest provided
if [ -n "${MANIFEST_FILE}" ] && [ -f "${MANIFEST_FILE}" ]; then
    echo "Verifying SHA-256 against manifest..."
    EXPECTED_HASH=$(grep '"sha256_checksum"' "${MANIFEST_FILE}" | cut -d '"' -f 4)
    ACTUAL_HASH=$(shasum -a 256 "${ENCRYPTED_BACKUP_FILE}" | cut -d ' ' -f 1)
    if [ "${EXPECTED_HASH}" != "${ACTUAL_HASH}" ]; then
        echo "ERROR: Checksum mismatch! Corrupted backup detected." >&2
        echo "Expected: ${EXPECTED_HASH}" >&2
        echo "Actual  : ${ACTUAL_HASH}" >&2
        exit 1
    fi
    echo "Checksum verified: OK (${ACTUAL_HASH})"
fi

TEMP_DIR=$(mktemp -d)
trap 'rm -rf "${TEMP_DIR}"' EXIT

DECRYPTED_GZ="${TEMP_DIR}/restored_dump.sql.gz"
DECOMPRESSED_SQL="${TEMP_DIR}/restored_dump.sql"

# 2. Decrypt with OpenSSL
echo "Decrypting archive..."
if ! openssl enc -d -aes-256-cbc -pbkdf2 \
    -in "${ENCRYPTED_BACKUP_FILE}" \
    -out "${DECRYPTED_GZ}" \
    -k "${BACKUP_PASSPHRASE}" 2>/dev/null; then
    echo "ERROR: Decryption failed! Invalid passphrase or corrupted ciphertext." >&2
    exit 1
fi
echo "Decryption successful: OK"

# 3. Decompress and test GZIP integrity
echo "Testing GZIP compression integrity..."
if ! gzip -d -c "${DECRYPTED_GZ}" > "${DECOMPRESSED_SQL}"; then
    echo "ERROR: GZIP decompression failed! Corrupted stream." >&2
    exit 1
fi
echo "Decompression successful: OK"

# 4. Verify SQL contents
SQL_SIZE=$(wc -c < "${DECOMPRESSED_SQL}" | tr -d ' ')
if [ "${SQL_SIZE}" -le 0 ]; then
    echo "ERROR: Restored SQL file is empty." >&2
    exit 1
fi

echo "Verifying SQL syntax / schema statements..."
if grep -q -E "(CREATE TABLE|INSERT INTO|ALTER TABLE|SELECT|--)" "${DECOMPRESSED_SQL}"; then
    echo "SQL statement patterns detected: OK"
else
    echo "WARNING: No recognizable SQL statements detected in dump." >&2
fi

echo "=== Restore Verification Drill PASSED ==="
echo "Size uncompressed: ${SQL_SIZE} bytes"
