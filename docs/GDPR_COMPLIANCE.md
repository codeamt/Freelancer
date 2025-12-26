# GDPR Compliance

This document describes the GDPR compliance features implemented in the application.

## Overview

The GDPR compliance system provides:
- Consent management for data processing
- Data subject access rights (DSAR)
- Data anonymization and pseudonymization
- Data retention policies
- Comprehensive audit logging
- Cookie consent management

## Features

### 1. Consent Management
- Granular consent for different data types
- Consent withdrawal and history tracking
- Expiration and renewal management
- Legal basis documentation

### 2. Data Subject Rights
- Right to access personal data
- Right to rectification
- Right to erasure (Right to be forgotten)
- Right to data portability
- Right to restrict processing
- Right to object

### 3. Data Anonymization
- Consistent pseudonymization
- Data masking capabilities
- Text anonymization
- JSON field anonymization

### 4. Retention Management
- Configurable retention policies
- Automatic cleanup of expired data
- Legal hold support
- Archive and delete actions

### 5. Audit Logging
- Complete audit trail
- Event categorization
- Severity tracking
- Compliance reporting

### 6. Cookie Consent
- Category-based consent
- Essential vs optional cookies
- Consent tracking per session/user
- Withdrawal support

## Implementation

### Database Schema

```sql
-- Consents
CREATE TABLE gdpr_consents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    consent_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    withdrawn_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- DSAR Requests
CREATE TABLE gdpr_dsar_requests (
    request_id VARCHAR(255) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    request_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details JSONB DEFAULT '{}'
);

-- Audit Log
CREATE TABLE gdpr_audit_log (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    user_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details JSONB DEFAULT '{}'
);

-- Retention Policies
CREATE TABLE gdpr_retention_policies (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    policy VARCHAR(20) NOT NULL,
    action VARCHAR(20) NOT NULL DEFAULT 'delete',
    conditions JSONB DEFAULT '{}'
);
```

### Usage Examples

#### Consent Management

```python
from core.gdpr import ConsentManager, ConsentType, ConsentStatus

# Initialize
consent_manager = ConsentManager(postgres_adapter)

# Record consent
await consent_manager.record_consent(
    user_id=123,
    consent_type=ConsentType.MARKETING,
    status=ConsentStatus.GRANTED,
    expires_at=datetime.utcnow() + timedelta(days=365),
    metadata={"ip_address": "192.168.1.1"}
)

# Check consent
has_consent = await consent_manager.check_consent(
    user_id=123,
    consent_type=ConsentType.MARKETING
)

# Withdraw consent
await consent_manager.withdraw_consent(
    user_id=123,
    consent_type=ConsentType.MARKETING,
    reason="User requested withdrawal"
)
```

#### Data Subject Rights

```python
from core.gdpr import DataSubjectRights, DSARType

# Initialize
dsr = DataSubjectRights(postgres_adapter, consent_manager)

# Export user data (Right to Access)
user_data = await dsr.get_user_data(user_id=123)

# Rectify data
await dsr.rectify_data(
    user_id=123,
    corrections={"email": "new@example.com"},
    reason="User requested update"
)

# Erase data (Right to be forgotten)
await dsr.erase_user_data(
    user_id=123,
    keep_essential=True,
    reason="GDPR erasure request"
)

# Export portable data
export_path = await dsr.export_user_data(
    user_id=123,
    format="json"
)

# Create DSAR request
request = await dsr.create_request(
    user_id=123,
    request_type=DSARType.ACCESS
)
```

#### Data Anonymization

```python
from core.gdpr import DataAnonymizer

# Initialize
anonymizer = DataAnonymizer()

# Anonymize email
email = anonymizer.anonymize_email("user@example.com")

# Anonymize phone
phone = anonymizer.anonymize_phone("+1-555-123-4567")

# Anonymize text
text = anonymizer.anonymize_text(
    "Contact John Doe at john@example.com or +1-555-123-4567"
)

# Anonymize JSON
data = anonymizer.anonymize_json({
    "name": "John Doe",
    "email": "john@example.com",
    "address": "123 Main St"
})

# Full user anonymization
await anonymizer.anonymize_user(user_id=123, postgres_adapter)
```

#### Retention Management

```python
from core.gdpr import RetentionManager, RetentionPolicy, DataCategory

# Initialize
retention = RetentionManager(postgres_adapter)

# Add retention rule
await retention.add_retention_rule(
    category=DataCategory.USER_ACTIVITY,
    policy=RetentionPolicy.DAYS_365,
    action="delete"
)

# Apply policies
results = await retention.apply_retention_policies()

# Place legal hold
await retention.place_legal_hold(
    user_id=123,
    data_type="user_profile",
    reason="Legal investigation",
    hold_until=datetime.utcnow() + timedelta(days=90)
)
```

#### Audit Logging

```python
from core.gdpr import GDPRAuditLogger, AuditEventType

# Initialize
audit_logger = GDPRAuditLogger(postgres_adapter)

# Log consent
await audit_logger.log_consent(
    user_id=123,
    consent_type="marketing",
    action="granted"
)

# Log data access
await audit_logger.log_data_access(
    user_id=123,
    accessed_by="admin",
    data_types=["profile", "activity"],
    purpose="Support request"
)

# Log data breach
await audit_logger.log_breach(
    breach_id="BR-2023-001",
    severity=AuditSeverity.HIGH,
    affected_users=150,
    data_types=["email", "name"],
    description="Unauthorized access to user data"
)

# Generate compliance report
report = await audit_logger.generate_compliance_report(days=30)
```

#### Cookie Consent

```python
from core.gdpr import CookieConsentManager, CookieCategory

# Initialize
cookie_manager = CookieConsentManager(postgres_adapter)

# Record consent
consent_id = await cookie_manager.record_consent(
    preferences={
        CookieCategory.NECESSARY: True,
        CookieCategory.ANALYTICS: True,
        CookieCategory.MARKETING: False
    },
    user_id=123,
    ip_address="192.168.1.1"
)

# Check category consent
has_analytics = await cookie_manager.check_category_consent(
    consent_id,
    CookieCategory.ANALYTICS
)

# Update consent
await cookie_manager.update_consent(
    consent_id,
    {CookieCategory.MARKETING: True}
)
```

## CLI Tool

The GDPR CLI tool provides command-line access to compliance features:

```bash
# Export user data
uv run python scripts/gdpr_manager.py export 123 --format json

# Anonymize user
uv run python scripts/gdpr_manager.py anonymize 123

# Delete user data
uv run python scripts/gdpr_manager.py delete 123

# Create DSAR request
uv run python scripts/gdpr_manager.py dsar 123 --type access

# Apply retention policies (dry run)
uv run python scripts/gdpr_manager.py retention --dry-run

# Show consent report
uv run python scripts/gdpr_manager.py consent --user-id 123

# Show audit trail
uv run python scripts/gdpr_manager.py audit 123 --days 30

# Place legal hold
uv run python scripts/gdpr_manager.py hold 123 --data-type profile --reason "Legal case"

# Generate compliance report
uv run python scripts/gdpr_manager.py report --days 30
```

## Best Practices

### 1. Consent Management
- Obtain explicit consent for non-essential processing
- Document legal basis for each data type
- Provide easy withdrawal mechanisms
- Keep consent history for audit

### 2. Data Minimization
- Collect only necessary data
- Anonymize/pseudonymize when possible
- Delete data when no longer needed
- Implement retention policies

### 3. Security Measures
- Encrypt personal data at rest
- Use secure connections in transit
- Implement access controls
- Regular security audits

### 4. User Rights
- Respond to DSARs within 30 days
- Provide data in portable format
- Allow easy withdrawal of consent
- Document all requests

### 5. Documentation
- Maintain processing records
- Document data flows
- Keep DPIA (Data Protection Impact Assessment)
- Update privacy policies

## Compliance Checklist

### Data Collection
- [ ] Legal basis identified for each data type
- [ ] Consent obtained where required
- [ ] Privacy notice provided
- [ ] Data minimization applied

### Data Processing
- [ ] Processing recorded in audit log
- [ ] Security measures implemented
- [ ] Access controls in place
- [ ] Data encryption enabled

### User Rights
- [ ] Access requests process documented
- [ ] Rectification procedure in place
- [ ] Erasure mechanism implemented
- [ ] Portability format defined

### Data Protection
- [ ] Retention policies configured
- [ ] Automated cleanup scheduled
- [ ] Legal hold process defined
- [ ] Backup encryption enabled

### Monitoring
- [ ] Audit logging enabled
- [ ] Breach detection in place
- [ ] Compliance reports generated
- [ ] Regular reviews scheduled

## Data Processing Categories

### User Profile Data
- Name, email, phone
- Address, bio
- Avatar, preferences
- **Retention**: 7 years (anonymized after)

### User Activity Data
- Login history
- Page views
- Actions performed
- **Retention**: 1 year (then deleted)

### Communication Data
- Emails sent
- Messages
- Notifications
- **Retention**: 2 years (then deleted)

### Analytics Data
- Behavior tracking
- Usage statistics
- Performance metrics
- **Retention**: 90 days (then deleted)

### Session Data
- Active sessions
- Tokens
- Device info
- **Retention**: 30 days (then deleted)

## Incident Response

### Data Breach Procedure
1. **Detection**
   - Monitor for unauthorized access
   - Review audit logs
   - User reports

2. **Assessment**
   - Determine scope
   - Identify affected data
   - Assess impact

3. **Containment**
   - Secure systems
   - Prevent further access
   - Preserve evidence

4. **Notification**
   - Notify supervisory authority (72 hours)
   - Inform affected individuals
   - Document notification

5. **Resolution**
   - Fix vulnerabilities
   - Review procedures
   - Update policies

## Privacy by Design

### Architecture
- Data minimization built-in
- Privacy settings default to private
- Granular consent controls
- Pseudonymization by default

### Development
- Privacy impact assessments
- Code reviews for privacy
- Testing with anonymized data
- Documentation of data flows

### Operations
- Least privilege access
- Regular audits
- Automated compliance checks
- Staff training

## International Transfers

### Adequacy Decisions
- Verify recipient country adequacy
- Use standard contractual clauses
- Implement additional safeguards
- Document transfer basis

### Cloud Services
- Choose GDPR-compliant providers
- Review processor agreements
- Ensure data location controls
- Monitor compliance

## Tools and Resources

### Python Libraries
- `faker` - Test data generation
- `cryptography` - Encryption
- `hashlib` - Hashing functions
- `secrets` - Secure tokens

### External Services
- GDPR compliance monitoring
- Data mapping tools
- Consent management platforms
- Breach detection services

### Documentation
- GDPR official text
- ICO guidelines
- EDPB recommendations
- Industry best practices

## Monitoring and Reporting

### Key Metrics
- Number of DSAR requests
- Average response time
- Data breaches reported
- Compliance violations

### Reports
- Monthly compliance summary
- Quarterly audit report
- Annual privacy report
- Ad hoc incident reports

### Alerts
- Failed consent checks
- Unauthorized access attempts
- Data retention violations
- Missing documentation
