from flask import Flask, request, Response, jsonify, stream_with_context
import time
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mock_server")

app = Flask(__name__)

# Mock data
VALID_CREDENTIALS = {
    "username": "testuser",
    "password": "password123"
}

MOCK_ACCESS_TOKEN = "mock_access_token"
MOCK_CONVERSATION_ID = "mock_conversation_id"

@app.route('/login', methods=['POST'])
def login():
    """Mock login endpoint."""
    data = request.json
    logger.info(f"Login request received: {data}")
    
    # Always return success for testing
    return jsonify({
        "access_token": MOCK_ACCESS_TOKEN,
        "token_type": "Bearer",
        "expires_in": 10800  # 3 hours
    })

@app.route('/conversations', methods=['POST'])
def create_conversation():
    """Mock create conversation endpoint."""
    auth_header = request.headers.get('Authorization')
    logger.info(f"Create conversation request received. Auth header: {auth_header}")
    
    # Always return success for testing
    return jsonify({
        "id": MOCK_CONVERSATION_ID,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Mock chat endpoint with streaming response."""
    auth_header = request.headers.get('Authorization')
    data = request.json
    logger.info(f"Chat request received. Auth header: {auth_header}")
    logger.info(f"Chat request data: {data}")
    
    conversation_id = data.get('conversation_id')
    message = data.get('message', "No message provided")
    
    # Always proceed for testing
    logger.info(f"Processing chat message: {message}")
    
    def generate():
        """Generate a streaming response."""
        # Start event
        yield 'event: start\n'
        yield 'data: {"status": "started"}\n\n'
        time.sleep(0.1)
        
        # Researching event
        yield 'event: researching\n'
        yield 'data: {"status": "researching"}\n\n'
        time.sleep(0.1)
        
        # Topics event
        yield 'event: topics\n'
        yield 'data: {"topics": {"summary": "Mock summary", "key_points": ["Point 1", "Point 2"], "topics": ["Topic 1", "Topic 2"]}}\n\n'
        time.sleep(0.1)
        
        # RAG event
        yield 'event: rag\n'
        yield 'data: {"status": "rag"}\n\n'
        time.sleep(0.1)
        
        # Progress events
        yield 'event: progress\n'
        yield 'data: {"message": "Searching laws for topic 1/2"}\n\n'
        time.sleep(0.1)
        
        yield 'event: progress\n'
        yield 'data: {"message": "Found relevant law"}\n\n'
        time.sleep(0.1)
        
        # Metadata event
        yield 'event: metadata\n'
        yield 'data: {"metadata": [{"title": "Mock Law Title", "source": "https://example.com/law"}]}\n\n'
        time.sleep(0.1)
        
        # Token events (content)
        yield 'event: token\n'
        yield 'data: {"content": "This is a "}\n\n'
        time.sleep(0.1)
        
        yield 'event: token\n'
        yield 'data: {"content": "mock response "}\n\n'
        time.sleep(0.1)
        
        yield 'event: token\n'
        yield 'data: {"content": "to your question: "}\n\n'
        time.sleep(0.1)
        
        yield 'event: token\n'
        yield 'data: {"content": "' + message + '"}\n\n'
        time.sleep(0.1)
        
        # Evals event
        yield 'event: progress\n'
        yield 'data: {"evals": "{\\"answer_faithfulness\\": 9, \\"answer_relevance\\": 10, \\"context_relevance\\": 8}"}\n\n'
        time.sleep(0.1)
        
        # End event
        yield 'event: end\n'
        yield 'data: {"status": "completed"}\n\n'
    
    return Response(stream_with_context(generate()), 
                   content_type='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
