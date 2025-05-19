#!/bin/bash

# Start the mock server in the background
echo "Starting mock server on http://localhost:5000..."
python mock_server.py > mock_server.log 2>&1 &
MOCK_SERVER_PID=$!

# Wait for the server to start
echo "Waiting for mock server to start..."
sleep 2

# Update the app.py to use the mock server
echo "Updating app.py to use mock server..."
sed -i.bak 's|BASE_URL = "https://testing.frag-das-gesetz.de"|BASE_URL = "http://localhost:5000"|g' app.py

# Run the Streamlit app
echo "Starting Streamlit app..."
streamlit run app.py

# Restore the original app.py
echo "Restoring original app.py..."
mv app.py.bak app.py

# Kill the mock server
echo "Stopping mock server..."
kill $MOCK_SERVER_PID
