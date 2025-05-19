import json
from typing import List, Dict, Any, Optional

class QuestionProcessor:
    """Processor for loading and managing test questions."""
    
    def __init__(self, questions_file: str):
        """Initialize the question processor.
        
        Args:
            questions_file: Path to the JSON file containing test questions.
        """
        self.questions_file = questions_file
        self.questions_by_category = {}
        self.load_questions()
        
    def load_questions(self) -> None:
        """Load questions from the JSON file."""
        try:
            with open(self.questions_file, 'r', encoding='utf-8') as f:
                self.questions_by_category = json.load(f)
        except Exception as e:
            print(f"Error loading questions: {e}")
            self.questions_by_category = {}
            
    def get_categories(self) -> List[str]:
        """Get the list of question categories.
        
        Returns:
            List[str]: The list of categories.
        """
        return list(self.questions_by_category.keys())
    
    def get_questions_by_category(self, category: str) -> List[str]:
        """Get the list of questions for a specific category.
        
        Args:
            category: The category to get questions for.
            
        Returns:
            List[str]: The list of questions.
        """
        return self.questions_by_category.get(category, [])
    
    def get_all_questions(self) -> List[Dict[str, str]]:
        """Get all questions with their categories.
        
        Returns:
            List[Dict[str, str]]: List of questions with category information.
        """
        all_questions = []
        for category, questions in self.questions_by_category.items():
            for question in questions:
                all_questions.append({
                    "category": category,
                    "question": question
                })
        return all_questions
    
    def get_questions_for_testing(self, categories: Optional[List[str]] = None) -> List[Dict[str, str]]:
        """Get questions for testing, optionally filtered by categories.
        
        Args:
            categories: Optional list of categories to include. If None, all categories are included.
            
        Returns:
            List[Dict[str, str]]: List of questions with category information.
        """
        if categories is None:
            return self.get_all_questions()
        
        filtered_questions = []
        for category in categories:
            questions = self.get_questions_by_category(category)
            for question in questions:
                filtered_questions.append({
                    "category": category,
                    "question": question
                })
        return filtered_questions
