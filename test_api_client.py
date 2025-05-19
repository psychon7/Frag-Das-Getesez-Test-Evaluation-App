import unittest
import asyncio
import subprocess
import time
import sys
import os
import signal
from api_client import APIClient

class TestAPIClient(unittest.TestCase):
    """Test the APIClient class with the mock server."""
    
    @classmethod
    def setUpClass(cls):
        """Start the mock server before running tests."""
        print("Starting mock server...")
        # Start the mock server as a subprocess
        cls.mock_server = subprocess.Popen(
            [sys.executable, "mock_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # Wait for the server to start
        time.sleep(2)
        
    @classmethod
    def tearDownClass(cls):
        """Stop the mock server after running tests."""
        print("Stopping mock server...")
        # Send SIGTERM to the mock server
        if cls.mock_server:
            if os.name == 'nt':  # Windows
                cls.mock_server.terminate()
            else:  # Unix/Linux/Mac
                os.kill(cls.mock_server.pid, signal.SIGTERM)
            cls.mock_server.wait()
    
    def setUp(self):
        """Set up the test environment."""
        self.api_client = APIClient("http://localhost:5000")
    
    def test_login(self):
        """Test login with valid credentials."""
        success = self.api_client.login("testuser", "password123")
        self.assertTrue(success)
        self.assertIsNotNone(self.api_client.access_token)
        self.assertTrue(self.api_client.is_token_valid())
        
        # Test login with invalid credentials
        invalid_client = APIClient("http://localhost:5000")
        success = invalid_client.login("invalid", "invalid")
        self.assertFalse(success)
    
    def test_create_conversation(self):
        """Test creating a conversation."""
        # Login first
        self.api_client.login("testuser", "password123")
        
        # Create conversation
        conversation_id = self.api_client.create_conversation()
        self.assertIsNotNone(conversation_id)
        self.assertEqual(conversation_id, "mock_conversation_id")
    
    def test_send_chat_message(self):
        """Test sending a chat message."""
        # Login first
        self.api_client.login("testuser", "password123")
        
        # Create conversation
        conversation_id = self.api_client.create_conversation()
        
        # Send chat message
        events = list(self.api_client.send_chat_message(conversation_id, "Test message"))
        
        # Check that we got events
        self.assertTrue(len(events) > 0)
        
        # Check for specific events
        event_types = [event["event"] for event in events if "event" in event]
        self.assertIn("start", event_types)
        self.assertIn("token", event_types)
        self.assertIn("end", event_types)
    
    def test_send_chat_message_async(self):
        """Test sending a chat message asynchronously."""
        # Login first
        self.api_client.login("testuser", "password123")
        
        # Create conversation
        conversation_id = self.api_client.create_conversation()
        
        # Send chat message asynchronously
        async def test_async():
            result = await self.api_client.send_chat_message_async(conversation_id, "Test message")
            return result
        
        result = asyncio.run(test_async())
        
        # Check result
        self.assertIn("content", result)
        self.assertIn("metadata", result)
        self.assertIn("evals", result)
        self.assertEqual(result["question"], "Test message")
        
        # Check content
        self.assertIn("Test message", result["content"])
        
        # Check metadata
        self.assertTrue(len(result["metadata"]) > 0)
        
        # Check evals
        self.assertIn("answer_faithfulness", result["evals"])
        self.assertIn("answer_relevance", result["evals"])
        self.assertIn("context_relevance", result["evals"])

if __name__ == "__main__":
    unittest.main()
