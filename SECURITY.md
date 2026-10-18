# Security Policy

## Supported Versions

Security updates and patches are actively maintained for the following versions of SesMetin Pro:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | Yes                |
| < 1.0.0 | No                 |

## Reporting a Vulnerability

We take the security of SesMetin Pro and its users seriously. If you discover a security vulnerability, please report it responsibly:

1. **Do not create a public issue** on GitHub.
2. Send an email to the repository maintainer via the contact information on [GitHub Profile](https://github.com/The0Sanity).
3. Provide a detailed summary of the issue, affected components, reproduction steps, and potential impact.
4. We will acknowledge receipt of your vulnerability report within 48 hours and work with you on a resolution before making any public disclosure.

## Security Architecture

- **100% Offline Processing**: All audio transcription, speaker diarization, and text normalization happen locally on the user machine without external API transmission.
- **Signed Binaries**: Windows executables (`SpeechToText.exe`) released via GitHub Actions are cryptographically signed with Authenticode certificates and published alongside SHA256 checksums (`SpeechToText.exe.sha256`).
- **Standard Storage**: User settings and configurations are stored strictly within OS-standard directories (`%APPDATA%\SesMetinPro\config.json`).
