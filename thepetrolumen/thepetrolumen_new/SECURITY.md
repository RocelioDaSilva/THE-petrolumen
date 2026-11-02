# Security Policy

## Reporting a Vulnerability

The PetroLúmen team and community take all security vulnerabilities seriously. Thank you for improving the security of PetroLúmen. We appreciate your efforts and responsible disclosure and will make every effort to acknowledge your contributions.

If you believe you have found a security vulnerability in PetroLúmen, please report it to us by emailing `security@example.com` (replace with a real address if this project were public) or by opening a GitHub issue with the "security" label if email is not appropriate for your disclosure.

Please include the following details with your report:
*   Description of the location and potential impact of the vulnerability.
*   A detailed description of the steps required to reproduce the vulnerability (POC scripts, screenshots, and compressed screen captures are all helpful).
*   Your name/handle and a link for recognition (e.g., Twitter or GitHub profile).

We will make an effort to respond within 72 hours to acknowledge receipt of your report.

## Security Best Practices for Developers & Users

### 1. Keep Dependencies Updated
Regularly update all dependencies for both the frontend (`npm audit fix` or `pnpm audit`) and backend (`pip list --outdated`, consider tools like `pip-audit` or `Dependabot`). Outdated dependencies are a common source of vulnerabilities.

### 2. Never Commit Secrets
API keys, database credentials, `SECRET_KEY` values, and other sensitive information should never be committed to the repository. Use environment variables or a `.env` file (which should be listed in `.gitignore`) to manage these.

### 3. Strong `SECRET_KEY` (Backend)
The `SECRET_KEY` used for signing JWTs and other security functions **MUST** be changed from the default placeholder value for any production or sensitive deployment. It should be a long, random, and unique string. You can generate one using:
```bash
openssl rand -hex 32
```
Store this securely, for example, in an environment variable or a `.env` file.

### 4. Input Validation
Ensure all user-supplied input is validated on both the frontend and backend to prevent common web vulnerabilities (e.g., XSS, SQL injection if raw SQL were ever used). FastAPI's Pydantic integration helps significantly with backend validation.

### 5. Secure Authentication & Authorization
*   Use strong, unique passwords.
*   Ensure authentication endpoints are protected against brute-force attacks (e.g., rate limiting).
*   Implement proper authorization checks to ensure users can only access resources and perform actions they are permitted to.

### 6. HTTPS
In production, always use HTTPS to encrypt communication between clients and the server.

### 7. Review Code
Conduct code reviews, especially for security-sensitive parts of the application.

### 8. Educate Yourself
Stay informed about common security threats and best practices in web development (e.g., OWASP Top 10).

### 9. API Key Management (for external services)
If the application integrates with external third-party services requiring API keys:
*   **Least Privilege**: Ensure API keys only have the minimum necessary permissions required for their function.
*   **Rotation**: Regularly rotate API keys according to the service provider's recommendations or your internal security policy.
*   **Monitoring**: Monitor API key usage for signs of abuse or compromise, if the service provider offers such tools.
*   **Secure Storage**: Store API keys securely using environment variables or a secrets management system (as mentioned in "Never Commit Secrets"). Do not embed them in code or configuration files directly accessible in the repository.

### 10. Data Handling Procedures
*   **Data Minimization**: Collect and retain only the data essential for the application's functionality. Avoid storing sensitive information if it's not strictly necessary.
*   **Encryption in Transit**: All external communication carrying sensitive data (including between frontend, backend, and any external services) must use HTTPS/TLS. Internal network communication between services should also be encrypted if possible.
*   **Encryption at Rest**: Sensitive data stored in databases or file systems should be encrypted. Leverage database-native encryption features where available and appropriate. For highly sensitive data, consider application-level encryption.
*   **Personally Identifiable Information (PII)**:
    *   Identify any PII the application handles.
    *   Apply stricter handling procedures for PII, including access controls and audit logging if feasible.
    *   Comply with relevant data privacy regulations (e.g., GDPR, CCPA) if applicable to your users.
*   **Access Control**: Implement robust access controls to ensure that data can only be accessed by authorized users and processes.
*   **Secure Data Disposal**: When data is no longer needed, ensure it is securely deleted and not just marked as inactive. This includes backups and archives, according to your data retention policy.

This `SECURITY.md` provides basic guidance. Security is an ongoing process, not a one-time setup.
