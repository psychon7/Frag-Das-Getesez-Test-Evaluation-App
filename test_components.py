import unittest
import json
import os
from question_processor import QuestionProcessor

class tionProcessor(unittest.TestCase):
    """Test the QuestionProcessor class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary test questions file
        self.test_file = "test_questions.json"
        self.test_data = {
            "Category1": ["Question1", "Question2"],
            "Category2": ["Question3", "Question4", "Question5"]
        }
        
        with open(self.test_file, "w") as f:
            json.dump(self.test_data, f)
        
        self.processor = QuestionProcessor(self.test_file)
    
    def tearDown(self):
        """Clean up after the test."""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
    
    def test_get_categories(self):
        """Test getting categories."""
        categories = self.processor.get_categories()
        self.assertEqual(set(categories), set(["Category1", "Category2"]))
    
    def test_get_questions_by_category(self):
        """Test getting questions by category."""
        questions = self.processor.get_questions_by_category("Category1")
        self.assertEqual(questions, ["Question1", "Question2"])
        
        questions = self.processor.get_questions_by_category("Category2")
        self.assertEqual(questions, ["Question3", "Question4", "Question5"])
        
        # Test non-existent category
        questions = self.processor.get_questions_by_category("NonExistentCategory")
        self.assertEqual(questions, [])
    
    def test_get_all_questions(self):
        """Test getting all questions."""
        questions = self.processor.get_all_questions()
        self.assertEqual(len(questions), 5)
        
        # Check that all questions are included
        question_texts = [q["question"] for q in questions]
        self.assertIn("Question1", question_texts)
        self.assertIn("Question2", question_texts)
        self.assertIn("Question3", question_texts)
        self.assertIn("Question4", question_texts)
        self.assertIn("Question5", question_texts)
        
        # Check that categories are correct
        for q in questions:
            if q["question"] in ["Question1", "Question2"]:
                self.assertEqual(q["category"], "Category1")
            else:
                self.assertEqual(q["category"], "Category2")
    
    def test_get_questions_for_testing(self):
        """Test getting questions for testing with category filtering."""
        # Test with specific categories
        questions = self.processor.get_questions_for_testing(["Category1"])
        self.assertEqual(len(questions), 2)
        
        question_texts = [q["question"] for q in questions]
        self.assertIn("Question1", question_texts)
        self.assertIn("Question2", question_texts)
        
        # Test with multiple categories
        questions = self.processor.get_questions_for_testing(["Category1", "Category2"])
        self.assertEqual(len(questions), 5)
        
        # Test with no categories (should return all questions)
        questions = self.processor.get_questions_for_testing(None)
        self.assertEqual(len(questions), 5)

if __name__ == "__main__":
    unittest.main()
