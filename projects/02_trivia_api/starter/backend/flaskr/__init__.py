import json
import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import func
import random
import sys

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, questions):
  page = request.args.get('page', 1, type=int)

  start = (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  formatted_questions = [question.format() for question in questions]
  return formatted_questions[start:end]


def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  CORS(app)

  '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, true')
    response.headers.add('Access-Control-Allow-Methods', 'GET, PUT, POST, DELETE, OPTIONS')
    return response

  '''
  @TODO: 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/categories')
  def get_categories():
    categories = Category.query.order_by(Category.id).all()
    formatted_categories = {category.id: category.type for category in categories}
    
    if len(formatted_categories) == 0:
      abort(404)

    return jsonify({
      'categories': formatted_categories
    })


  '''
  @TODO: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''
  @app.route('/questions')
  def get_questions():
    questions = Question.query.order_by(Question.id).all()
    questions_count = len(Question.query.all())
    categories = Category.query.order_by(Category.id).all()
    formatted_questions = paginate_questions(request, questions)

    if len(formatted_questions) == 0:
      abort(404)

    return jsonify({
      'questions': formatted_questions,
      'total_questions': questions_count,
      'categories': {category.id: category.type for category in categories},
      'current_category': None
    })

  '''
  @TODO: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    try:
      question = Question.query.get(question_id)

      if not question:
        abort(404)
      
      question.delete()

      return jsonify({
        'deleted': question_id
      })
    except:
      abort(422)

  '''
  @TODO: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''
  @app.route('/questions', methods=['POST'])
  def create_question():
    body = request.get_json()

    # import pdb;pdb.set_trace()

    question = body.get('question')
    answer = body.get('answer')
    category = body.get('category')
    difficulty = body.get('difficulty')
    search = body.get('searchTerm')

    try:
      if search:
        questions = Question.query.order_by(Question.id).filter(Question.question.ilike(f'%{search}%')).all()
        total_questions = len(questions)
        current_category = None
        formatted_questions = [question.format() for question in questions]

        return jsonify({
          'questions': formatted_questions,
          'total_questions': total_questions,
          'current_category': current_category
        })
      else:
        new_question = Question(
          question=question,
          answer=answer,
          category=category,
          difficulty=difficulty
        )
        new_question.insert()

        return jsonify({
          'created': new_question.id
        }), 201
    except:
      print(sys.exc_info())
      abort(422)

  '''
  @TODO: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''

  '''
  @TODO: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route('/categories/<int:category_id>/questions')
  def get_questions_by_category(category_id):
    questions = Question.query.filter(Question.category == str(category_id)).all()
    total_questions = len(questions)
    current_category = Category.query.get(category_id)

    if not current_category:
      abort(404)

    formatted_questions = [question.format() for question in questions]

    return jsonify({
      'questions': formatted_questions,
      'total_questions': total_questions,
      'current_category': current_category.type
    })

  '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  @app.route('/quizzes', methods=['POST'])
  def get_quizzes():
    body = request.get_json()

    previous_questions = body.get('previous_questions')
    quiz_category = body.get('quiz_category').get('id')

    if len(previous_questions):
      if quiz_category:
        question = Question.query.filter(Question.id.notin_(previous_questions), Question.category == quiz_category).order_by(func.random()).first()
      else:
        question = Question.query.filter(Question.id.notin_(previous_questions)).order_by(func.random()).first()

    else:
      if quiz_category:
        question = Question.query.filter(Question.category == quiz_category).order_by(func.random()).first()
      else:
        question = Question.query.order_by(func.random()).first()
    
    if question:
      question = question.format()
    
    return jsonify({
      'question': question
    })

  '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      'error': 404,
      'message': 'Not found'
    }), 404
  
  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      'error': 422,
      'message': 'unprocessable'
    }), 422
  
  return app

    