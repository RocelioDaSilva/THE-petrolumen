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

This `SECURITY.md` provides basic guidance. Security is an ongoing process, not a one-time setup.
