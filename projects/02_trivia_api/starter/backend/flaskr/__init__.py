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
    CORS(app)

    @app.after_request
    def after_request(response):
        response.headers.add(
            'Access-Control-Allow-Headers',
            'Content-Type, Authorization, true'
        )
        response.headers.add(
            'Access-Control-Allow-Methods',
            'GET, PUT, POST, DELETE, OPTIONS'
        )
        return response

    @app.route('/categories')
    def get_categories():
        categories = Category.query.order_by(Category.id).all()
        formatted_categories = {
            category.id: category.type for category in categories
        }

        if len(formatted_categories) == 0:
            abort(404)

        return jsonify({
            'categories': formatted_categories
        })

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
            'categories': {
                category.id: category.type for category in categories
            },
            'current_category': None
        })

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
        except Exception:
            abort(422)

    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()

        question = body.get('question')
        answer = body.get('answer')
        category = body.get('category')
        difficulty = body.get('difficulty')
        search = body.get('searchTerm')

        try:
            if search:
                questions = Question.query.order_by(
                    Question.id).filter(
                            Question.question.ilike(f'%{search}%')
                        ).all()
                total_questions = len(questions)
                current_category = None
                formatted_questions = [
                    question.format() for question in questions
                ]

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
        except Exception:
            print(sys.exc_info())
            abort(422)

    @app.route('/categories/<int:category_id>/questions')
    def get_questions_by_category(category_id):
        questions = Question.query.filter(
            Question.category == str(category_id)
        ).all()
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

    @app.route('/quizzes', methods=['POST'])
    def get_quizzes():
        body = request.get_json()

        previous_questions = body.get('previous_questions')
        quiz_category = body.get('quiz_category').get('id')

        if len(previous_questions):
            if quiz_category:
                question = Question.query.filter(
                        Question.id.notin_(previous_questions),
                        Question.category == quiz_category
                    ).order_by(func.random()).first()
            else:
                question = Question.query.filter(
                        Question.id.notin_(previous_questions)
                    ).order_by(func.random()).first()

        else:
            if quiz_category:
                question = Question.query.filter(
                        Question.category == quiz_category
                    ).order_by(func.random()).first()
            else:
                question = Question.query.order_by(func.random()).first()

        if question:
            question = question.format()

        return jsonify({
            'question': question
        })

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
