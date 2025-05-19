import requests
import time
import json
import asyncio
from typing import Dict, Any, Optional, Tuple, List, Generator
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("api_client")

class APIClient:
    """Client for interacting with the Frag Das Getesez Chat API."""
    
    def __init__(self, base_url: str):
        """Initialize the API client.
        
        Args:
            base_url: The base URL of the API.
        """
        self.base_url = base_url
        self.access_token = None
        self.token_expiry = 0  # Unix timestamp when token expires
    
    def login(self, username: str, password: str) -> bool:
        """Login to the API and get an access token.
        
        Args:
            username: The username for authentication.
            password: The password for authentication.
            
        Returns:
            bool: True if login was successful, False otherwise.
        """
        url = f"{self.base_url}/login"
        payload = {
            "username": username,
            "password": password
        }
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Extract token from response
            self.access_token = data.get("access_token")
            
            # Set token expiry (3 hours from now)
            self.token_expiry = time.time() + (3 * 60 * 60)
            
            return True
        except requests.exceptions.RequestException as e:
            print(f"Login failed: {e}")
            return False
    
    def is_token_valid(self) -> bool:
        """Check if the current token is valid.
        
        Returns:
            bool: True if token is valid, False otherwise.
        """
        return self.access_token is not None and time.time() < self.token_expiry
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers with authorization token.
        
        Returns:
            Dict[str, str]: Headers with authorization token.
        """
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def create_conversation(self) -> Optional[str]:
        """Create a new conversation.
        
        Returns:
            Optional[str]: The conversation ID if successful, None otherwise.
        """
        if not self.is_token_valid():
            print("Token expired or not available")
            return None
        
        url = f"{self.base_url}/conversations"
        
        try:
            response = requests.post(url, headers=self.get_headers())
            response.raise_for_status()
            data = response.json()
            
            # Extract conversation ID from response
            return data.get("id")
        except requests.exceptions.RequestException as e:
            print(f"Failed to create conversation: {e}")
            return None
    
    def send_chat_message(self, conversation_id: str, message: str) -> Optional[Dict[str, Any]]:
        """Send a message to the chat endpoint.
        
        Args:
            conversation_id: The ID of the conversation.
            message: The message to send.
            
        Returns:
            Optional[Dict[str, Any]]: The response data if successful, None otherwise.
        """
        if not self.is_token_valid():
            print("Token expired or not available")
            return None
        
        url = f"{self.base_url}/chat"
        payload = {
            "conversation_id": conversation_id,
            "file_id": "",
            "message": message
        }
        
        try:
            response = requests.post(url, json=payload, headers=self.get_headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to send chat message: {e}")
            return None
            
    async def send_chat_message_async(self, conversation_id: str, message: str) -> Dict[str, Any]:
        """Send a chat message to the API asynchronously and process the streaming response.
        
        Args:
            conversation_id: The ID of the conversation.
            message: The message to send.
            
        Returns:
            Dict[str, Any]: The processed response data.
        """
        if not self.is_token_valid():
            logger.error("Token expired or not available")
            return {
                "error": "Token expired or not available",
                "content": "",
                "metadata": [],
                "evals": {},
                "question": message,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            }
        
        url = f"{self.base_url}/chat"
        payload = {
            "conversation_id": conversation_id,
            "file_id": "",  # Include file_id even if empty
            "message": message
        }
        
        try:
            logger.info(f"Sending chat message: {message}")
            logger.debug(f"Request payload: {payload}")
            logger.debug(f"Headers: {self.get_headers()}")
            
            # Use requests for streaming response
            response = requests.post(
                url, 
                json=payload, 
                headers=self.get_headers(),
                stream=True,
                timeout=60
            )
            
            # Check for error response
            if response.status_code != 200:
                try:
                    error_details = response.json()
                    logger.error(f"API error: {response.status_code} - {error_details}")
                except:
                    logger.error(f"API error: {response.status_code} - {response.text}")
            
            response.raise_for_status()
            
            # Process the streaming response
            content_parts = []
            metadata = []
            evals = {}
            
            # Read the response as a stream
            buffer = b''
            for chunk in response.iter_content(chunk_size=1024):
                if not chunk:
                    continue
                    
                buffer += chunk
                lines = buffer.split(b'\n')
                buffer = lines.pop()  # Keep the last incomplete line in the buffer
                
                for line in lines:
                    if not line:
                        continue
                        
                    try:
                        line_str = line.decode('utf-8')
                        logger.debug(f"Received line: {line_str}")
                        
                        # Parse SSE format
                        if line_str.startswith('data:'):
                            data_str = line_str[5:].strip()
                            if not data_str:  # Skip empty data
                                continue
                                
                            try:
                                data = json.loads(data_str)
                                
                                # Handle token events (content)
                                if 'content' in data and data['content']:
                                    content = str(data['content']).strip()
                                    if content:
                                        content_parts.append(content)
                                        
                                # Handle metadata events
                                if 'metadata' in data and data['metadata']:
                                    if isinstance(data['metadata'], list):
                                        metadata.extend(data['metadata'])
                                    else:
                                        metadata.append(data['metadata'])
                                        
                                # Handle evals events
                                if 'evals' in data and data['evals']:
                                    try:
                                        # The evals might be a string representation of JSON
                                        if isinstance(data['evals'], str):
                                            evals_data = json.loads(data['evals'].replace("'", '"'))
                                            evals.update(evals_data)
                                        else:
                                            evals.update(data['evals'])
                                    except Exception as e:
                                        logger.error(f"Error parsing evals: {e}")
                                        
                            except json.JSONDecodeError as e:
                                logger.error(f"Error decoding JSON: {e}")
                                logger.error(f"Problematic data: {data_str}")
                    except UnicodeDecodeError as e:
                        logger.error(f"Error decoding line: {e}")
            
            # Process any remaining data in the buffer
            if buffer:
                try:
                    line_str = buffer.decode('utf-8')
                    if line_str.startswith('data:'):
                        data_str = line_str[5:].strip()
                        if data_str:
                            try:
                                data = json.loads(data_str)
                                if 'content' in data and data['content']:
                                    content_parts.append(str(data['content']).strip())
                            except json.JSONDecodeError:
                                pass
                except UnicodeDecodeError:
                    pass
            
            # Combine all content parts and clean up
            full_content = ''.join([str(c) for c in content_parts if c])
            
            logger.info(f"Processed response for message: {message}")
            logger.info(f"Content length: {len(full_content)}")
            logger.info(f"Metadata items: {len(metadata)}")
            
            return {
                "content": full_content,
                "metadata": metadata,
                "evals": evals,
                "question": message,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(error_msg)
            return {
                "error": error_msg,
                "content": f"Error: {str(e)}",
                "metadata": [],
                "evals": {},
                "question": message,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            }
