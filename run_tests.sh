#!/bin/bash

# Run component tests
echo "Running component tests..."
python test_components.py

# Run API client tests with mock server
echo "Running API client tests..."
python test_api_client.py

echo "All tests completed."
