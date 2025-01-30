# User Data Schema Documentation

## Overview

This document provides comprehensive documentation for the user data schema used in the application. The schema defines the structure and validation rules for user data, ensuring consistency and data integrity across the system.

## Schema Structure

### Core User Fields

#### Required Fields

| Field          | Type   | Description                    | Validation Rules                                                  |
| -------------- | ------ | ------------------------------ | ----------------------------------------------------------------- |
| `id`           | string | Unique identifier              | Must match pattern: `^[0-9a-fA-F]{24}$` (MongoDB ObjectId format) |
| `email`        | string | User's email address           | Must be valid email format                                        |
| `firstName`    | string | User's first name              | 1-50 characters                                                   |
| `lastName`     | string | User's last name               | 1-50 characters                                                   |
| `passwordHash` | string | Bcrypt hash of user's password | Exactly 60 characters                                             |
| `status`       | string | Account status                 | Must be one of: "active", "inactive", "pending", "suspended"      |
| `createdAt`    | string | Creation timestamp             | ISO 8601 date-time format                                         |
| `updatedAt`    | string | Last update timestamp          | ISO 8601 date-time format                                         |

#### Optional Profile Information

```json
"profile": {
  "avatar": "URL to profile image",
  "bio": "User biography (max 500 chars)",
  "dateOfBirth": "YYYY-MM-DD"
}
```

### Contact Information

```json
"contact": {
  "phone": "E.164 format phone number",
  "address": {
    "street": "Street address",
    "city": "City name",
    "state": "State/Province",
    "postalCode": "Postal code",
    "country": "Country name"
  }
}
```

### User Preferences

```json
"preferences": {
  "language": "ISO language code (e.g., en-US)",
  "timezone": "IANA timezone (e.g., America/New_York)",
  "notifications": {
    "email": true/false,
    "push": true/false,
    "sms": true/false
  }
}
```

## Data Population Guidelines

### User Status Management

The status field supports four states:
- `active`: Regular user with full access
- `inactive`: User account dormant but can be reactivated
- `pending`: New account awaiting verification
- `suspended`: Account temporarily blocked

### Date and Time Handling

- All dates must use ISO 8601 format
- Dates without times: `YYYY-MM-DD`
- Timestamps with timezone: `YYYY-MM-DDThh:mm:ssZ`
- Always store timestamps in UTC

### Phone Number Formatting

- Must follow E.164 format
- Example: `+14155552671`
- Includes:
  - Plus sign (+)
  - Country code
  - Area code
  - Local number

### Language and Locale

Language codes must follow the format:
- Two-letter language code (ISO 639-1)
- Two-letter country code (ISO 3166-1)
- Example: `en-US`, `fr-FR`, `ja-JP`

## Practical Applications

### 1. User Management Systems
- User registration and profile management
- Account status tracking
- User preferences storage
- Contact information management

### 2. Authentication & Authorization
- Password hash storage for secure authentication
- Status-based access control
- Account verification workflows

### 3. Internationalization
- Language preference storage
- Timezone-aware features
- Localized content delivery

### 4. Communication Systems
- Multi-channel notification preferences
- Contact information validation
- Address standardization

### 5. Analytics and Reporting
- User demographics analysis
- Account status monitoring
- Registration trend analysis
- Geographic distribution reports

## Validation and Testing

### Using the Validation Script

```bash
# Install required package
pip install jsonschema

# Run validation
python validate_users.py
```

The script provides:
- Individual validation for each user
- Detailed error messages
- Summary statistics
- Non-zero exit code for validation failures

### Common Validation Scenarios

1. **Email Validation**
   - Must be valid email format
   - Uniqueness should be enforced at database level

2. **Password Hash Validation**
   - Must be exactly 60 characters (bcrypt format)
   - Should contain only valid bcrypt characters

3. **Date Validation**
   - Must parse as valid ISO 8601
   - Future dates may be invalid for birth dates
   - Creation date must be before update date

## Best Practices

1. **Data Security**
   - Never store plain text passwords
   - Validate email addresses before storing
   - Sanitize all user-provided content

2. **Data Integrity**
   - Always validate against schema before storing
   - Maintain audit trail using timestamps
   - Enforce required fields at application level

3. **Performance Considerations**
   - Index frequently queried fields
   - Consider partial updates for large objects
   - Cache frequently accessed user data

4. **Extensibility**
   - Use optional fields for flexible data structure
   - Follow schema versioning practices
   - Document all schema changes

## Schema Evolution

### Handling Schema Updates

1. Version your schema changes
2. Maintain backward compatibility
3. Provide migration scripts for existing data
4. Document breaking changes
5. Consider gradual rollout of schema changes

### Future Considerations

- Adding support for multiple addresses
- Enhanced security features
- Additional notification channels
- Custom user fields
- Social media integration

## Tools and Integration

### Development Tools
- JSON Schema validators
- Data migration scripts
- Test data generators
- Schema documentation generators

### API Integration
- RESTful endpoints for CRUD operations
- GraphQL schema integration
- Webhook notifications for updates
- Batch import/export capabilities

## Conclusion

This schema provides a robust foundation for user data management while maintaining flexibility for future extensions. Regular validation ensures data integrity, while the structured format supports various use cases from basic user management to complex analytics.