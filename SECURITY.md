# PizzaCone Security Hardening Guide

## OWASP Top 10 Implementation

This document outlines the security hardening measures implemented in the PizzaCone project based on the OWASP Top 10 vulnerabilities.

---

## 1. Broken Access Control

### Implementation
- **Session Security**: All session cookies are set with `HttpOnly` and `Secure` flags
- **CSRF Protection**: Cross-Site Request Forgery tokens are enforced
- **Access Control**: All dashboard views use `@login_required` and `@user_passes_test` decorators
- **Password Requirements**: Minimum 12 characters with complexity validation

### Files Modified
- `pizzacone_project/settings.py`: Session cookie security settings
- `dashboard/views.py`: Decorator-based access control

### Best Practices
1. Always use `@login_required` on protected views
2. Use `@user_passes_test` for role-based access
3. Check permissions in templates: `{% if user.is_staff %}`

---

## 2. Cryptographic Failures

### Implementation
- **HTTPS Enforcement**: Configured `SECURE_SSL_REDIRECT` for production
- **HSTS**: HTTP Strict Transport Security enabled (1 year)
- **Secure Cookies**: All cookies marked as Secure in production
- **Secret Key Management**: Loaded from environment variables

### Files Modified
- `pizzacone_project/settings.py`: HTTPS and cryptography settings
- `.env.example`: Environment variable template

### Best Practices
1. Never commit SECRET_KEY to version control
2. Use environment variables for all secrets
3. Keep Django and dependencies updated
4. Run `python manage.py check --deploy` before production

---

## 3. Injection

### Implementation
- **SQL Injection Prevention**: Always use Django ORM, never raw SQL
- **XSS Prevention**: Templates automatically escape output
- **Input Sanitization**: Utility functions provided in `core/security_utils.py`
- **CSRF Tokens**: Enforced on all forms

### Files Modified
- `core/security_utils.py`: Input sanitization functions
- `menu/models.py`: File upload validation

### Safe Query Examples
```python
# SAFE - Use ORM
User.objects.filter(username=username)

# SAFE - Use parameterized queries if raw SQL needed
User.objects.raw('SELECT * FROM auth_user WHERE username = %s', [username])

# UNSAFE - Never do this!
User.objects.raw(f'SELECT * FROM auth_user WHERE username = {username}')
```

---

## 4. Insecure Design

### Implementation
- **Security Headers**: X-Frame-Options, X-Content-Type-Options configured
- **Content Security Policy**: Restrictive CSP headers set
- **Secure Defaults**: Debug disabled by default in production
- **Input Validation**: File upload validation implemented

### Files Modified
- `pizzacone_project/settings.py`: Security header configuration

### Configuration
```python
# Content Security Policy
SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ["'self'"],
    'script-src': ["'self'", "'unsafe-inline'"],
    'style-src': ["'self'", "'unsafe-inline'"],
    # ... more restrictive settings
}
```

---

## 5. Security Misconfiguration

### Implementation
- **Debug Mode**: Disabled by default, controlled via environment variable
- **Allowed Hosts**: Configured via environment variable
- **Security Checks**: Run `python manage.py check --deploy`
- **File Upload Limits**: 5MB maximum file size
- **Logging Configuration**: Comprehensive logging with rotation

### Files Modified
- `pizzacone_project/settings.py`: Security configuration
- `.env.example`: Configuration template

### Checklist
- [ ] Set DEBUG=False in production
- [ ] Configure ALLOWED_HOSTS
- [ ] Set SECRET_KEY from environment
- [ ] Run deployment checks: `python manage.py check --deploy`

---

## 6. Vulnerable and Outdated Components

### Implementation
- **Dependency Management**: All packages specified in `requirements.txt`
- **Pillow**: Used for safe image processing
- **Django 6.0.7**: Latest stable version

### Maintenance
1. Regular updates: `pip list --outdated`
2. Security audit: `pip-audit` (install: `pip install pip-audit`)
3. Check for vulnerabilities: `safety check`

### Commands
```bash
# Check for security vulnerabilities
pip-audit

# Update packages safely
pip install --upgrade pip setuptools wheel
pip install -U -r requirements.txt
```

---

## 7. Identification and Authentication Failures

### Implementation
- **Rate Limiting**: 5 login attempts per hour per IP
- **Password Validation**: 12-character minimum, complexity checks
- **Session Timeout**: 2 weeks with secure cookie settings
- **User Access Control**: Staff-only dashboard protection

### Files Modified
- `pizzacone_project/settings.py`: Authentication settings
- `dashboard/views.py`: Rate limiting decorator on login

### Rate Limiting
```python
@ratelimit(key='ip', rate='5/h', method='POST', block=True)
def staff_login(request):
    # Login view with rate limiting
    pass
```

---

## 8. Software and Data Integrity Failures

### Implementation
- **Signed Cookies**: Session cookies are cryptographically signed
- **Data Validation**: Form validation and model clean() methods
- **CSRF Tokens**: All state-changing operations protected
- **Integrity Checks**: Database constraints via Django ORM

### Files Modified
- `pizzacone_project/settings.py`: Signing configuration
- `menu/models.py`: Data validation in clean() methods

---

## 9. Logging and Monitoring Failures

### Implementation
- **Comprehensive Logging**: File-based logging with rotation
- **Security Logging**: Dedicated security.log for security events
- **Log Rotation**: 10MB max file size with 10 backups
- **Django Security Logging**: Captured from django.security logger

### Files Modified
- `pizzacone_project/settings.py`: Logging configuration
- Log files: `logs/django.log`, `logs/security.log`

### Accessing Logs
```bash
# View recent logs
tail -f logs/django.log
tail -f logs/security.log

# Search logs
grep "WARNING\|ERROR" logs/security.log
```

---

## 10. Server-Side Request Forgery (SSRF)

### Implementation
- **File Upload Validation**: Whitelist allowed file types and extensions
- **File Size Limits**: 5MB maximum upload
- **MIME Type Validation**: Check against allowed MIME types
- **Network Isolation**: Database restricted to localhost

### Files Modified
- `core/security_utils.py`: File validation functions
- `pizzacone_project/settings.py`: File upload limits
- `menu/models.py`: Validation in clean() method

### File Upload Validation
```python
from core.security_utils import validate_file_upload

# In models
def clean(self):
    if self.image:
        validate_file_upload(self.image)

# Allowed types configured in settings.py
ALLOWED_FILE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
```

---

## Environment Setup

### Development Environment
1. Create `.env` file from `.env.example`:
   ```bash
   cp .env.example .env
   ```

2. Update `.env` with development values:
   ```env
   SECRET_KEY=your-dev-secret-key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   ENVIRONMENT=development
   ```

### Production Environment
1. Generate a secure SECRET_KEY:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

2. Set production environment variables:
   ```env
   SECRET_KEY=<generated-key>
   DEBUG=False
   ALLOWED_HOSTS=yourdomain.com
   ENVIRONMENT=production
   SECURE_SSL_REDIRECT=True
   SESSION_COOKIE_SECURE=True
   CSRF_COOKIE_SECURE=True
   ```

---

## Security Testing

### Local Testing
```bash
# Django security check
python manage.py check --deploy

# Run tests
python manage.py test

# Code quality check
pip install flake8 bandit
flake8 .
bandit -r . --skip B101,B601
```

### Vulnerability Scanning
```bash
# Check for known vulnerabilities
pip install safety
safety check

# Audit dependencies
pip install pip-audit
pip-audit
```

---

## Security Checklist

### Development
- [ ] Read this security guide
- [ ] Use environment variables for secrets
- [ ] Never use raw SQL queries
- [ ] Validate all file uploads
- [ ] Use Django ORM only

### Before Production Deployment
- [ ] Run: `python manage.py check --deploy`
- [ ] Generate and set new SECRET_KEY
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS
- [ ] Enable HTTPS
- [ ] Set secure cookie flags
- [ ] Run security audit tools
- [ ] Review logs configuration
- [ ] Set up monitoring

### Ongoing
- [ ] Monitor logs regularly
- [ ] Keep dependencies updated
- [ ] Run security audits monthly
- [ ] Review access logs
- [ ] Update emergency contacts
- [ ] Test disaster recovery

---

## Common Vulnerabilities to Avoid

### 1. SQL Injection
```python
# ❌ NEVER
query = f"SELECT * FROM menu_menuitem WHERE name = '{user_input}'"

# ✅ ALWAYS
MenuItem.objects.filter(name=user_input)
```

### 2. Cross-Site Scripting (XSS)
```html
<!-- ❌ NEVER use |safe filter unnecessarily -->
{{ user_input|safe }}

<!-- ✅ ALWAYS let Django escape output -->
{{ user_input }}
```

### 3. CSRF Attacks
```html
<!-- ✅ ALWAYS include CSRF token in forms -->
<form method="POST">
    {% csrf_token %}
    <!-- form fields -->
</form>
```

### 4. Insecure Direct Object References
```python
# ❌ NEVER trust user input directly
item = MenuItem.objects.get(pk=request.GET['id'])

# ✅ ALWAYS validate access
item = get_object_or_404(MenuItem, pk=pk)
if not request.user.is_staff:
    raise PermissionDenied()
```

---

## Resources

- [OWASP Top 10 2021](https://owasp.org/Top10/)
- [Django Security Documentation](https://docs.djangoproject.com/en/6.0/topics/security/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/)
- [OWASP Cheat Sheets](https://cheatsheetseries.owasp.org/)

---

## Questions or Issues?

If you discover a security vulnerability, please **do not** open a public issue. Instead, contact the security team immediately.

For security questions, refer to the [Django Security Page](https://www.djangoproject.com/weblog/2018/dec/02/security-releases-issued/) for responsible disclosure guidelines.
