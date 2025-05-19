# Frag Das Getesez Test Evaluation App

This Streamlit application tests legal questions against an API and evaluates the responses. It allows you to:

1. Authenticate with the API
2. Send test questions to the chat endpoint
3. Process responses and extract evaluation scores
4. Display results in a table
5. Download results as a CSV file

## Features

- Authentication with username and password
- Parallel processing of questions (configurable up to 5 concurrent requests)
- Category-based filtering of test questions
- Real-time progress tracking
- Results table with question, response, metadata, and evaluation scores
- CSV export functionality

## Setup

1. Clone this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

### Production Mode

To run the application with the real API:

```bash
./run.sh
```

or

```bash
streamlit run app.py
```

### Testing Mode

To run the application with a mock server for testing:

```bash
./run_with_mock.sh
```

## Usage

1. **Login**: The app will automatically use the default credentials (testuser/password123)
2. **Configure Test**: Select categories to test and set the number of parallel requests
3. **Run Test**: Click the "Run Test" button to start processing questions
4. **View Results**: Once processing is complete, view the results in the table
5. **Download Results**: Click the "Download Results as CSV" button to save the results

## File Structure

- `app.py`: Main Streamlit application
- `api_client.py`: Client for interacting with the API
- `parallel_handler.py`: Handler for sending parallel requests
- `question_processor.py`: Processor for loading and managing test questions
- `testquestions.json`: JSON file containing test questions
- `requirements.txt`: List of required Python packages
- `mock_server.py`: Mock server for testing
- `test_components.py`: Unit tests for components
- `test_api_client.py`: Unit tests for API client
- `run.sh`: Script to run the application
- `run_tests.sh`: Script to run all tests
- `run_mock_server.sh`: Script to run the mock server
- `run_with_mock.sh`: Script to run the application with the mock server

## API Endpoints Used

- `/login`: Authenticate and get access token
- `/conversations`: Create a new conversation
- `/chat`: Send messages to the chat endpoint

## Testing

To run the tests:

```bash
./run_tests.sh
```

To run the mock server separately:

```bash
./run_mock_server.sh
```

## Notes

- The access token expires after 3 hours
- The same conversation ID is used for all questions in a test run
- Responses are streamed and concatenated to form the complete response
- Evaluation scores are extracted from the "evals" field in the response
