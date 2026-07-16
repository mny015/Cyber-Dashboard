-- Fernet-protected TOTP secrets are longer than the original plaintext value.
-- Keep the secret nullable for accounts that have not started MFA enrollment.
ALTER TABLE users
    MODIFY COLUMN mfa_secret VARCHAR(255) NULL;
