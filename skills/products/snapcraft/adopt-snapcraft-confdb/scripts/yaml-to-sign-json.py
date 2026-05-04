#!/usr/bin/env python3
import sys
import json
import yaml
from datetime import datetime, timezone

def yaml_to_sign_json(yaml_file):
    """Convert YAML assertion draft to JSON for snap sign"""
    with open(yaml_file, 'r') as f:
        data = yaml.safe_load(f)
    
    # Ensure type is set
    if 'type' not in data:
        data['type'] = 'confdb-schema'
    
    # Ensure authority-id matches account-id if not present
    if 'authority-id' not in data and 'account-id' in data:
        data['authority-id'] = data['account-id']
    
    # Add timestamp if not present (mandatory field)
    if 'timestamp' not in data:
        data['timestamp'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Ensure revision is a string (snap sign expects string headers)
    if 'revision' in data:
        data['revision'] = str(data['revision'])
    
    # Handle body field - keep it as a string
    if 'body' in data:
        body_content = data['body']
        # If it's already a string, keep it
        # If it's a dict/object, convert to JSON string
        if not isinstance(body_content, str):
            data['body'] = json.dumps(body_content, indent=2)
    
    # Convert views to proper format if needed
    if 'views' in data and isinstance(data['views'], dict):
        # Keep views as is - snap sign handles dict format
        pass
    
    # Remove fields that snap sign will add
    for field in ['body-length', 'sign-key-sha3-384']:
        if field in data:
            del data[field]
    
    # Ensure type is first
    result = {'type': data['type']}
    for key, value in data.items():
        if key != 'type':
            result[key] = value
    
    return result

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: yaml-to-sign-json.py <yaml-file>", file=sys.stderr)
        sys.exit(1)
    
    result = yaml_to_sign_json(sys.argv[1])
    print(json.dumps(result, indent=2))
