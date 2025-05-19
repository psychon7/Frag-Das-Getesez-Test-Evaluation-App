import streamlit as st
import pandas as pd
import asyncio
import json
import os
import time
import sys
from typing import List, Dict, Any, Optional
import nest_asyncio
from streamlit_ace import st_ace
import logging

# Apply nest_asyncio to allow running asyncio in Streamlit
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

try:
    nest_asyncio.apply()
except RuntimeError:
    # If there's no event loop, create one
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    nest_asyncio.apply()

from api_client import APIClient
from parallel_handler import ParallelRequestHandler
from question_processor import QuestionProcessor

# Constants
BASE_URL = "https://testing.frag-das-gesetz.de"
DEFAULT_USERNAME = "testuser"
DEFAULT_PASSWORD = "password123"
QUESTIONS_FILE = "testquestions.json"

# Initialize session state
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "api_client" not in st.session_state:
    st.session_state.api_client = None
if "results" not in st.session_state:
    st.session_state.results = []
if "progress" not in st.session_state:
    st.session_state.progress = 0
if "total_questions" not in st.session_state:
    st.session_state.total_questions = 0
if "editing_questions" not in st.session_state:
    st.session_state.editing_questions = False
if "questions_json" not in st.session_state:
    st.session_state.questions_json = ""
if "processing" not in st.session_state:
    st.session_state.processing = False

def load_test_questions() -> str:
    """Load test questions from file."""
    try:
        with open(QUESTIONS_FILE, 'r') as f:
            return f.read()
    except Exception as e:
        logging.error(f"Error loading test questions: {e}")
        return "{}"

def save_test_questions(content: str) -> bool:
    """Save test questions to file."""
    try:
        # Validate JSON
        json.loads(content)
        
        # Write to file
        with open(QUESTIONS_FILE, 'w') as f:
            f.write(content)
        return True
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON format: {e}")
        return False
    except Exception as e:
        st.error(f"Error saving test questions: {e}")
        return False

def initialize_api_client() -> bool:
    """Initialize the API client if not already initialized."""
    if st.session_state.api_client is not None:
        return True
    
    api_client = APIClient(BASE_URL)
    
    # Login
    if api_client.login(DEFAULT_USERNAME, DEFAULT_PASSWORD):
        st.session_state.api_client = api_client
        
        # Create a new conversation
        conversation_id = api_client.create_conversation()
        if conversation_id:
            st.session_state.conversation_id = conversation_id
            return True
    
    return False

def update_progress(current: int, total: int, question: str, result: Dict[str, Any]) -> None:
    """Update the progress in the session state."""
    progress = current / total
    st.session_state.progress = progress
    
    # Ensure result has required fields
    if "content" not in result:
        result["content"] = ""
    if "metadata" not in result:
        result["metadata"] = []
    if "evals" not in result:
        result["evals"] = {}
    if "index" not in result:
        result["index"] = current - 1
    if "timestamp" not in result:
        result["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    # Update or add the result
    updated = False
    for i, existing_result in enumerate(st.session_state.results):
        if existing_result.get("index") == result["index"]:
            st.session_state.results[i] = result
            updated = True
            break
    
    if not updated:
        st.session_state.results.append(result)

def run_test(
    categories: List[str], 
    max_parallel: int
) -> None:
    """Run the test with the selected categories and parallel requests."""
    # Ensure API client is initialized
    if not initialize_api_client():
        st.error("Failed to initialize API client. Please check your connection and try again.")
        return
    
    # Reset results
    st.session_state.results = []
    st.session_state.progress = 0
    st.session_state.processing = True
    
    # Get questions for testing
    question_processor = QuestionProcessor(QUESTIONS_FILE)
    questions_data = question_processor.get_questions_for_testing(categories)
    questions = [q["question"] for q in questions_data]
    
    st.session_state.total_questions = len(questions)
    
    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Create parallel handler
        handler = ParallelRequestHandler(st.session_state.api_client, max_parallel)
        
        # Process questions
        results = loop.run_until_complete(
            handler.process_questions(
                st.session_state.conversation_id,
                questions,
                update_progress
            )
        )
        
        # Update results with category information
        for i, result in enumerate(results):
            result["category"] = questions_data[i]["category"]
        
        st.session_state.results = results
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        logger.error(f"Error in run_test: {str(e)}", exc_info=True)
    finally:
        st.session_state.processing = False
        loop.close()

def format_metadata(metadata: List[Dict[str, Any]]) -> str:
    """Format metadata for display in the table."""
    if not metadata:
        return "No metadata available"
    
    try:
        formatted = []
        for item in metadata:
            if isinstance(item, dict):
                title = item.get("title", "")
                source = item.get("source", "")
                if title or source:
                    formatted.append(f"• {title}" + (f"\n  {source}" if source else ""))
            elif isinstance(item, str):
                formatted.append(f"• {item}")
        
        return "\n\n".join(formatted) if formatted else "No valid metadata"
    except Exception as e:
        logger.error(f"Error formatting metadata: {e}")
        return f"Error: {str(e)}"

def format_evals(evals: Dict[str, Any]) -> str:
    """Format evaluation scores for display in the table."""
    if not evals:
        return "No evaluation scores"
    
    try:
        # Handle case where evals might be a string
        if isinstance(evals, str):
            try:
                evals = json.loads(evals)
            except json.JSONDecodeError:
                return evals  # Return as is if it's not valid JSON
        
        formatted = []
        for key, value in evals.items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False, indent=2)
            formatted.append(f"• {key}: {value}")
        
        return "\n".join(formatted)
    except Exception as e:
        logging.error(f"Error formatting evals: {e}")
        return f"Error: {str(e)}"

def create_results_dataframe() -> pd.DataFrame:
    """Create a DataFrame from the results for display and download."""
    data = []
    
    for i, result in enumerate(st.session_state.results):
        try:
            # Ensure all required fields exist
            if not isinstance(result, dict):
                logging.warning(f"Result {i} is not a dictionary: {result}")
                continue
                
            # Safely get values with defaults
            question = str(result.get("question", f"Question {i+1}"))
            content = str(result.get("content", ""))
            
            # Handle metadata
            metadata = result.get("metadata")
            if metadata is None:
                metadata = []
            elif not isinstance(metadata, (list, dict)):
                metadata = [str(metadata)]
                
            # Handle evals
            evals = result.get("evals", {})
            if not isinstance(evals, dict):
                try:
                    if isinstance(evals, str):
                        evals = json.loads(evals)
                    else:
                        evals = {"score": str(evals)}
                except (json.JSONDecodeError, TypeError):
                    evals = {"score": str(evals)}
            
            data.append({
                "#": i + 1,
                "Question": question,
                "Response": content,
                "Metadata": format_metadata(metadata),
                "Eval Scores": format_evals(evals),
                "Category": result.get("category", ""),
                "Timestamp": result.get("timestamp", "")
            })
            
        except Exception as e:
            logging.error(f"Error processing result {i}: {e}", exc_info=True)
            data.append({
                "#": i + 1,
                "Question": f"Error processing question {i+1}",
                "Response": f"Error: {str(e)}",
                "Metadata": "",
                "Eval Scores": "",
                "Category": "",
                "Timestamp": ""
            })
    
    # Create DataFrame with consistent column order
    columns = ["#", "Question", "Response", "Metadata", "Eval Scores", "Category", "Timestamp"]
    df = pd.DataFrame(data, columns=columns)
    
    return df.fillna("")

def main():
    st.title("Frag Das Getesez Test Evaluation App")
    
    # Sidebar
    st.sidebar.header("Test Configuration")
    
    # Add edit questions button
    if st.sidebar.button("Edit Test Questions"):
        st.session_state.editing_questions = True
        st.session_state.questions_json = load_test_questions()
    
    # Check if we're in editing mode
    if st.session_state.editing_questions:
        st.header("Edit Test Questions")
        st.write("Edit the JSON below to add, modify, or remove test questions. The format should be a JSON object with categories as keys and arrays of questions as values.")
        
        # Add the Ace editor for JSON
        edited_content = st_ace(
            value=st.session_state.questions_json,
            language="json",
            theme="monokai",
            key="ace_editor",
            height=400,
            font_size=14,
            show_gutter=True,
            wrap=True,
            auto_update=True,
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save Changes"):
                if save_test_questions(edited_content):
                    st.success("Test questions saved successfully!")
                    st.session_state.editing_questions = False
                    st.experimental_rerun()
        with col2:
            if st.button("Cancel"):
                st.session_state.editing_questions = False
                st.experimental_rerun()
                
        # Show a preview of the questions
        try:
            questions_data = json.loads(edited_content)
            st.subheader("Preview")
            for category, questions in questions_data.items():
                with st.expander(f"{category} ({len(questions)} questions)"):
                    for i, question in enumerate(questions):
                        st.write(f"{i+1}. {question}")
        except json.JSONDecodeError:
            st.error("Invalid JSON format. Please fix the errors before saving.")
            
        # Stop here if in editing mode
        return
    
    # Initialize API client in the background
    initialize_api_client()
    
    # Load question categories
    question_processor = QuestionProcessor(QUESTIONS_FILE)
    categories = question_processor.get_categories()
    
    # Category selection
    selected_categories = st.sidebar.multiselect(
        "Select Categories",
        categories,
        default=categories
    )
    
    # Parallel requests
    max_parallel = st.sidebar.slider(
        "Max Parallel Requests",
        min_value=1,
        max_value=5,
        value=3,
        help="Maximum number of parallel requests to send to the API"
    )
    
    # Add a note about processing time
    st.sidebar.info("⏱️ Processing the test may take up to 5 minutes depending on the number of questions and API response time.")
    
    # Run test button
    if st.button("Run Test", disabled=st.session_state.processing):
        if not selected_categories:
            st.warning("Please select at least one category.")
        else:
            # Run the test
            run_test(selected_categories, max_parallel)
    
    # Progress bar and status
    progress_bar = st.empty()
    status_text = st.empty()
    results_table = st.empty()
    
    if st.session_state.processing:
        progress = st.session_state.progress
        progress_text = f"Processing {int(progress * st.session_state.total_questions)} of {st.session_state.total_questions} questions... ({progress:.0%})"
        progress_bar.progress(progress)
        status_text.text(progress_text)
    
    # Results section
    if st.session_state.results and not st.session_state.processing:
        st.header("Test Results")
        
        # Create DataFrame
        df = create_results_dataframe()
        
        # Add instructions for dataframe interaction

        
        # Display results table with enhanced features
        st.dataframe(
            df.reset_index(drop=True),  # Reset index instead of using hide_index
            height=600  # Larger height for better visibility
        )
        
        # Add some spacing
        st.write("")
        
        # Download button
        csv = df.to_csv(index=False, encoding='utf-8-sig')  # Add BOM for Excel compatibility
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name=f"test_results_{int(time.time())}.csv",
            mime="text/csv",
            help="Download the results as a CSV file"
        )

if __name__ == "__main__":
    main()
