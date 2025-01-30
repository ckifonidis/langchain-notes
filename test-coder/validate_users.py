#!/usr/bin/env python3
import json
from jsonschema import validate, ValidationError, SchemaError
import sys

def load_json_file(file_path):
    """Load and parse a JSON file."""
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file '{file_path}': {str(e)}")
        sys.exit(1)

def validate_users(schema_path, users_path):
    """Validate users JSON against the schema."""
    # Load schema and users data
    schema = load_json_file(schema_path)
    users_data = load_json_file(users_path)

    if not isinstance(users_data, dict) or 'users' not in users_data:
        print("Error: Users file must contain a 'users' array.")
        return False

    # Track validation status
    all_valid = True
    valid_count = 0
    invalid_count = 0

    # Validate each user
    for i, user in enumerate(users_data['users'], 1):
        try:
            validate(instance=user, schema=schema)
            valid_count += 1
            print(f"✓ User {i} ({user.get('email', 'No email')}) is valid")
        except ValidationError as e:
            all_valid = False
            invalid_count += 1
            print(f"✗ User {i} ({user.get('email', 'No email')}) is invalid:")
            print(f"  - Path: {' -> '.join(str(p) for p in e.path)}")
            print(f"  - Error: {e.message}")
        except SchemaError as e:
            print(f"Error in schema: {e.message}")
            sys.exit(1)

    # Print summary
    print("\nValidation Summary:")
    print(f"Total users processed: {valid_count + invalid_count}")
    print(f"Valid users: {valid_count}")
    print(f"Invalid users: {invalid_count}")
    
    return all_valid

def main():
    """Main function to run validation."""
    schema_path = 'schemas/user-schema.json'
    users_path = 'data/sample-users.json'

    print("Starting user data validation...")
    try:
        if validate_users(schema_path, users_path):
            print("\nSuccess: All users are valid!")
            sys.exit(0)
        else:
            print("\nWarning: Some users are invalid!")
            sys.exit(1)
    except Exception as e:
        print(f"\nError during validation: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()