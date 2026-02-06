#!/usr/bin/env python3
"""
Test script to verify website validation improvements.
"""

from src.services.validation_service import ValidationService

# Test websites from your CSV that were incorrectly marked as invalid
test_websites = [
    "verveinterio.com",
    "urbanindiadesign.com",
    "heavenbirdinteriors.com",
    "petalsartdecor.com",
    "sculptdesignstudio.com",
    "dezineinnovation.com",
    "baaniinteriors.com",
    "peafowlstudio.co.in",
    "buildprointerior.com",
    "3dspaceinteriors.com",
]

print("Testing Website Validation")
print("=" * 80)

validator = ValidationService()

valid_count = 0
invalid_count = 0

for website in test_websites:
    is_valid = validator.validate_website(website)
    status = "✓ VALID" if is_valid else "✗ INVALID"
    print(f"{website:<40} {status}")
    
    if is_valid:
        valid_count += 1
    else:
        invalid_count += 1

print("=" * 80)
print(f"Results: {valid_count} valid, {invalid_count} invalid out of {len(test_websites)} tested")
print(f"Success rate: {(valid_count/len(test_websites))*100:.1f}%")
