# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Here are the versions that are currently being supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0.0 | :x:                |

## Reporting a Vulnerability

We take the security of Git Flow Action seriously. If you believe you have found a security vulnerability, please report it to us as described below.

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to security@your-domain.com.

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

Please include the following information in your report:

- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

This information will help us triage your report more quickly.

## Security Measures

### GitHub Token Security

- The action requires a GitHub token for certain operations
- Tokens are never logged or exposed in any way
- Tokens are only used for the specific operations they are needed for
- We recommend using the minimum required permissions for the token

### Git Operations Security

- All Git operations are performed with proper authentication
- Tags and branches are created with appropriate permissions
- No sensitive information is included in commit messages or tags
- Git configuration is properly sanitized

### Input Validation

- All user inputs are validated before use
- Version numbers are checked for proper semantic versioning format
- Branch names and commit messages are sanitized
- Configuration values are validated against expected formats

### Dependencies

- We regularly update dependencies to their latest secure versions
- Dependencies are pinned to specific versions
- Security vulnerabilities in dependencies are addressed promptly
- We use GitHub's security scanning features to monitor for vulnerabilities

## Best Practices

When using this action, we recommend:

1. Using the latest stable version
2. Regularly updating to new versions
3. Using the minimum required permissions for GitHub tokens
4. Reviewing the action's code before use
5. Monitoring the repository for security updates
6. Using secure commit messages
7. Following Git Flow best practices

## Updates

Security updates will be released as patch versions (e.g., 1.0.0 -> 1.0.1). We will notify users of security updates through:

1. GitHub Security Advisories
2. Release notes
3. Repository announcements

## Contact

If you have any questions about security, please contact us at security@your-domain.com.
