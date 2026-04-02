# Security Policy

## Overview

CineCraft is a local-first desktop application that processes video files entirely on your machine. This document outlines security considerations and best practices.

## Security Principles

1. **Local Processing Only** - No data is sent to external servers
2. **Open Source** - All code is publicly available for review
3. **User Control** - You choose what files are processed and how
4. **Privacy First** - No tracking, telemetry, or data collection

## Supported Versions

| Version | Status | Support |
|---------|--------|---------|
| 1.x     | Current | Security updates |
| 0.x     | EOL    | Not supported |

## Reporting Security Issues

If you discover a security vulnerability in CineCraft, please report it responsibly:

### Do Not
- ❌ Post security issues publicly on GitHub
- ❌ Share exploits or proof-of-concepts publicly
- ❌ Attempt unauthorized access

### Do
- ✅ Email security details to: `[your-security-email]@example.com`
- ✅ Include version number and steps to reproduce
- ✅ Allow time for a fix before public disclosure (30 days recommended)

### Response Timeline
- **Day 1:** Initial acknowledgment
- **Days 1-7:** Investigation and fix development
- **Days 7-14:** Testing and verification
- **Day 14-30:** Patch release and announcement

## Security Features

### Application Level

**Input Validation**
```python
# All file inputs validated before processing
def validate_file_path(filepath):
    # Check file exists
    # Check file extension
    # Check file size limits
    # Prevent path traversal
    pass
```

**Process Isolation**
- FFmpeg runs in isolated subprocess
- Controlled command arguments
- No shell interpretation of user input

**Error Handling**
- Errors logged locally, not sent externally
- Sensitive paths removed from error messages
- User-friendly error messages

### System Level

**Permissions**
- Runs with user permissions only
- No admin/root required
- Respects OS file system permissions

**File Access**
- Only accesses files you explicitly select
- No hidden file access
- No automatic scanning of directories

**Network**
- No internet connection required
- FastAPI server binds to localhost only
- No external API calls

## Known Limitations

### What We Can't Protect Against

1. **Malicious Files**
   - FFmpeg may have vulnerabilities with malformed files
   - Keep FFmpeg updated
   - Scan source files if from untrusted sources

2. **System Security**
   - If your OS is compromised, CineCraft can be compromised
   - Keep Windows/Mac/Linux updated
   - Use antivirus software

3. **Physical Access**
   - Anyone with computer access can use CineCraft
   - Protect your device with passwords/encryption

4. **Supply Chain**
   - Verify CineCraft.exe hash before running
   - Download from official GitHub releases only
   - Check file signatures if available

## Best Practices

### General Use

```
✅ DO:
  • Keep FFmpeg updated
  • Keep Windows/Mac/Linux updated
  • Use official CineCraft releases
  • Verify checksums of downloaded files
  • Scan untrusted video files before processing
  • Backup important files before processing
  • Review FFmpeg command in debug logs

❌ DON'T:
  • Download from unofficial sources
  • Ignore antivirus warnings
  • Process files from untrusted sources without scanning
  • Run with admin privileges
  • Disable Windows Defender or antivirus
  • Download pre-built executables without verification
```

### Development

```
✅ DO:
  • Review code before contributions
  • Use virtual environments
  • Keep dependencies updated
  • Report security issues responsibly
  • Sign commits with GPG
  • Use strong passwords for GitHub

❌ DON'T:
  • Include hardcoded credentials
  • Add unnecessary dependencies
  • Use eval() or exec()
  • Process untrusted code
  • Disable security checks
  • Commit sensitive data
```

## Dependency Security

### Current Dependencies

```
fastapi>=0.115,<1.0        - Web framework
uvicorn>=0.35,<1.0         - ASGI server
pywebview>=5.4,<6.0        - GUI framework
pyinstaller>=6.0,<7.0      - Build tool
```

### Dependency Update Process

1. Check for security advisories
2. Run `pip audit` to scan for vulnerabilities
3. Test with new versions in dev environment
4. Update requirements.txt
5. Create release notes documenting changes

### Command to Check Dependencies

```bash
# Install pip-audit
pip install pip-audit

# Check for vulnerabilities
pip-audit

# Only update requirements
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt
```

## FFmpeg Security

### FFmpeg Vulnerabilities

FFmpeg is maintained by a dedicated security team. Check for updates:

```bash
# Check current version
ffmpeg -version

# Update FFmpeg
# Windows: Download from https://ffmpeg.org/download.html
# macOS: brew upgrade ffmpeg
# Linux: sudo apt update && sudo apt upgrade ffmpeg
```

### Safe FFmpeg Command Construction

```python
# SAFE: Using list (no shell interpretation)
command = ["ffmpeg", "-i", input_file, output_file]
subprocess.run(command)

# UNSAFE: Using string with shell=True
command = f"ffmpeg -i {input_file} {output_file}"
subprocess.run(command, shell=True)  # DON'T DO THIS
```

**CineCraft always uses safe command construction** (list format, shell=False).

## Encryption & Data Protection

### Local Files

- **No encryption by default** - CineCraft doesn't encrypt files
- **File system protection** - Use OS encryption (BitLocker, FileVault, dm-crypt)
- **Temporary files** - Created in system temp folder, deleted after processing

### Temporary Files

```python
# CineCraft may create temporary files
# These are stored in:
# Windows: C:\Users\[User]\AppData\Local\Temp
# macOS: /var/folders/.../T
# Linux: /tmp

# Files are:
# - Deleted after processing
# - Readable/writable by owner only
# - Not encrypted
```

## Testing Security

### Manual Security Audit

```bash
# Check for hardcoded passwords
grep -r "password" --include="*.py" .
grep -r "token" --include="*.py" .
grep -r "api_key" --include="*.py" .

# Check for dangerous functions
grep -r "eval\|exec\|__import__" --include="*.py" .

# Scan for SQL injection risks
grep -r "execute\|query" --include="*.py" .

# Check imports
pip-audit
```

### Code Review Checklist

Before merging code:
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] No dangerous functions used
- [ ] Error handling appropriate
- [ ] Third-party dependencies reviewed
- [ ] Security tests added

## Vulnerability Disclosure

### If You Find a Vulnerability

1. **Do NOT post on GitHub Issues**
2. **Email:** `security@example.com`
3. **Include:**
   - Vulnerability description
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Coordinated Disclosure

- We will:
  - Acknowledge receipt within 24 hours
  - Investigate and develop a fix
  - Create a patch release
  - Credit the reporter (if desired)
- You agree to:
  - Allow time for investigation and patching
  - Not disclose publicly before patch release
  - Work with us on responsible disclosure

## Security Roadmap

### Current Release (v1.0.0)
- ✅ Input validation
- ✅ Safe command construction
- ✅ Local processing only
- ✅ No external network calls
- ✅ Error handling

### Future Versions
- [ ] Code signing for executables
- [ ] Integrity verification
- [ ] Advanced file validation
- [ ] Security audit by third party
- [ ] Two-factor authentication option

## Legal Disclaimer

CineCraft is provided "AS IS" without warranty of any kind. Users are responsible for:

1. **Compliance** - Ensuring your use complies with local laws
2. **Content** - You have rights to process your video files
3. **Updates** - Keeping your system and dependencies updated
4. **Backups** - Backing up important files

## References

- [OWASP Security Guidelines](https://owasp.org/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [FFmpeg Security](https://ffmpeg.org/security.html)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)

## FAQ

### Q: Is my data sent anywhere?
**A:** No. CineCraft runs entirely offline on your computer.

### Q: Can CineCraft infect my computer?
**A:** CineCraft itself cannot. However, download from official sources only.

### Q: Should I trust this project?
**A:** You can audit the open-source code. We recommend reviewing the code and understanding what it does.

### Q: What if I find a security issue?
**A:** Report it responsibly to security@example.com (do not post publicly).

### Q: How can I verify the .exe is safe?
**A:** 
1. Check digital signature (right-click → Properties)
2. Verify file hash from official release
3. Run in antivirus scanner
4. Compare file size and creation date

### Q: Can you encrypt my videos?
**A:** Not currently. Use OS-level encryption for sensitive files.

### Q: Is FFmpeg safe?
**A:** Yes, same FFmpeg used by VLC, OBS, and many professional tools. Keep updated.

---

## Contact

- **Security Issues:** [security-email]@example.com
- **General Questions:** GitHub Discussions
- **Bug Reports:** GitHub Issues

---

**Last Updated:** v1.0.0  
**Next Review:** 2025-Q2

*This security policy is subject to change. Users will be notified of significant updates.*
