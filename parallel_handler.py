import asyncio
from typing import List, Dict, Any, Optional
import time
import logging
from api_client import APIClient

# Configure logging
logger = logging.getLogger("parallel_handler")

class ParallelRequestHandler:
    """Handler for sending parallel requests to the API."""
    
    def __init__(self, api_client: APIClient, max_parallel: int = 5, max_retries: int = 3, retry_delay: int = 2):
        """Initialize the parallel request handler.
        
        Args:
            api_client: The API client to use for requests.
            max_parallel: The maximum number of parallel requests to send.
            max_retries: The maximum number of retries for failed requests.
            retry_delay: The delay between retries in seconds.
        """
        self.api_client = api_client
        self.max_parallel = min(max_parallel, 5)  # Ensure max is 5
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
    async def process_questions(
        self, 
        conversation_id: str, 
        questions: List[str],
        progress_callback=None
    ) -> List[Dict[str, Any]]:
        """Process a list of questions in parallel.
        
        Args:
            conversation_id: The ID of the conversation.
            questions: The list of questions to process.
            progress_callback: Optional callback function to report progress.
            
        Returns:
            List[Dict[str, Any]]: The list of responses.
        """
        # Create a semaphore to limit the number of parallel requests
        semaphore = asyncio.Semaphore(self.max_parallel)
        
        async def process_question(question: str, index: int) -> Dict[str, Any]:
            """Process a single question with semaphore control and retry logic."""
            async with semaphore:
                start_time = time.time()
                
                # Initialize result
                result = None
                
                # Retry logic
                for retry in range(self.max_retries):
                    try:
                        logger.info(f"Processing question {index+1}/{len(questions)}: {question}")
                        logger.info(f"Attempt {retry+1}/{self.max_retries}")
                        
                        # Ensure we're running in the correct event loop
                        try:
                            result = await self.api_client.send_chat_message_async(conversation_id, question)
                        except RuntimeError as e:
                            if "no running event loop" in str(e):
                                # Create a new event loop if none exists
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                result = await self.api_client.send_chat_message_async(conversation_id, question)
                            else:
                                raise
                        
                        # Check if there was an error
                        if "error" in result:
                            logger.error(f"Error in response: {result['error']}")
                            if retry < self.max_retries - 1:
                                logger.info(f"Retrying in {self.retry_delay} seconds...")
                                await asyncio.sleep(self.retry_delay)
                                continue
                        
                        # If we got here, the request was successful or we've exhausted retries
                        break
                        
                    except Exception as e:
                        logger.error(f"Exception while processing question: {e}", exc_info=True)
                        if retry < self.max_retries - 1:
                            logger.info(f"Retrying in {self.retry_delay} seconds...")
                            await asyncio.sleep(self.retry_delay)
                        else:
                            logger.error(f"Failed after {self.max_retries} attempts")
                            result = {
                                "error": str(e),
                                "content": f"Error after {self.max_retries} attempts: {str(e)}",
                                "metadata": [],
                                "evals": {},
                                "question": question
                            }
                
                end_time = time.time()
                
                # If result is still None after all retries, create an error result
                if result is None:
                    result = {
                        "error": "Failed to get response after all retries",
                        "content": "Failed to get response after all retries",
                        "metadata": [],
                        "evals": {},
                        "question": question
                    }
                
                # Add processing time and question index
                result["processing_time"] = end_time - start_time
                result["index"] = index
                result["question"] = question  # Ensure question is included
                
                # Call progress callback if provided
                if progress_callback:
                    progress_callback(index + 1, len(questions), question, result)
                    
                return result
        
        # Create tasks for all questions
        tasks = [
            process_question(question, i) 
            for i, question in enumerate(questions)
        ]
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results, handling any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Task for question {i+1} failed with exception: {result}")
                processed_results.append({
                    "question": questions[i],
                    "content": f"Error: {str(result)}",
                    "metadata": [],
                    "evals": {},
                    "error": str(result),
                    "index": i
                })
            else:
                processed_results.append(result)
        
        # Sort results by original index
        processed_results.sort(key=lambda x: x["index"])
        
        return processed_results
