import os
import unittest
import json

from flask.wrappers import Response
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


DB_HOST = os.getenv('DB_HOST', '127.0.0.1:5432')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgresql://{}:{}@{}/{}".format(DB_USER, DB_PASSWORD, DB_HOST, self.database_name)
        setup_db(self.app, self.database_path)

        self.new_question = {
            'question': 'Which is the only team to play in every soccer World Cup tournament?',
            'answer': 'Brazil',
            'difficulty': 3,
            'category': 6
        }

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
    
    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """
    def test_get_all_categories(self):
        response = self.client().get('/categories')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['categories'])

    def test_get_paginated_questions(self):
        response = self.client().get('/questions')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['total_questions'])
        self.assertTrue(len(data['questions']))
    
    def test_404_sent_requesting_beyond_valid_page(self):
        response = self.client().get('/questions?page=1000')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['message'], 'Not found')
    
    def test_delete_question(self):
        question = Question(
            question=self.new_question['question'],
            answer=self.new_question['answer'],
            difficulty=self.new_question['difficulty'],
            category=self.new_question['category']
        )

        question.insert()
        id = question.id

        response = self.client().delete(f'/questions/{id}')
        data = json.loads(response.data)

        question = Question.query.filter(Question.id == id).one_or_none()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['deleted'], id)
        self.assertEqual(question, None)
    
    def test_422_if_question_does_not_exist(self):
        response = self.client().delete('/questions/200')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 422)
        self.assertEqual(data['message'], 'unprocessable')
    
    def test_create_question(self):
        response = self.client().post('/questions', json=self.new_question)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(data['created'])
    
    def test_422_create_invalid_question(self):
        invalid_question = {
            'question': 'invalid',
            'answer': 'invalid',
            'category': 'invalid',
            'difficulty': 'invalid'
        }

        response = self.client().post('/questions', json=invalid_question)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 422)
        self.assertEqual(data['message'], 'unprocessable')
    
    def test_get_questions_by_category(self):
        response = self.client().get('/categories/6/questions')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(data['questions']))
    
    def test_404_get_questios_by_invalid_category(self):
        response = self.client().get('/categories/1000/questions')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['message'], 'Not found')

    def test_valid_search(self):
        response = self.client().post('/questions', json={'searchTerm': 'which'})
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(data['questions']))
    
    def test_empty_search_return_all_questions(self):
        response = self.client().post('/questions', json={'searchTerm': 'which'})
        data = json.loads(response.data)
        
        all_questions = len(Question.query.all())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data['questions']), all_questions)
    
    def test_get_quizz_question(self):
        body = {
            'previous_questions': [2, 3],
            'quiz_category': {
                'type': 'Entertainment',
                'id': '6'
            }
        }
        response = self.client().post('/quizzes', json=body)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['question'])
    
    def test_return_empty_question_by_sending_invalid_category(self):
        body = {
            'previous_questions': [2, 3],
            'quiz_category': {
                'type': 'Entertainment',
                'id': '600'
            }
        }

        response = self.client().post('/quizzes', json=body)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(data['question'])


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()