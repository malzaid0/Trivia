import os
from flask import Flask, request, abort, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,DELETE')
        return response

    """
  HOME
  """

    @app.route('/')
    def index_page():
        return redirect(url_for('get_questions'))

    """
  CATEGORIES
  """

    @app.route('/categories', methods=['GET'])
    def get_categories():
        categories = Category.query.all()
        formatted_categories = {category.id: category.type for category in categories}
        return jsonify({
            'success': True,
            'categories': formatted_categories
        })

    """
  QUESTIONS
  """

    @app.route('/questions', methods=['GET'])
    def get_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        categories = Category.query.all()
        formatted_categories = {category.id: category.type for category in categories}

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(Question.query.all()),
            'categories': formatted_categories,
            'current_category': None
        })

    """
  DELETE QUESTION
  """

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            del_question = Question.query.filter(Question.id == question_id).one_or_none()

            if del_question is None:
                abort(404)

            del_question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'deleted': question_id,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            })

        except:
            abort(422)

    """
  POST QUESTION
  """

    @app.route('/questions', methods=['POST'])
    def post_question():
        data = request.get_json()

        new_question = data.get('question', None)
        new_answer = data.get('answer', None)
        new_category = data.get('category', None)
        new_difficulty = data.get('difficulty', None)

        try:
            question = Question(question=new_question, answer=new_answer, category=new_category,
                                difficulty=new_difficulty)
            question.insert()

            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'created': question.id,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            })

        except:
            abort(422)

    """
  SEARCH QUESTION
  """

    @app.route('/questions/search', methods=['POST'])
    def search_question():
        data = request.get_json()
        try:
            search_term = data.get('searchTerm', None)

            selection = Question.query.filter(Question.question.ilike('%' + search_term + '%')).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(selection)
            })

        except:
            abort(422)

    """
  QUESTIONS FROM CATEGORY
  """

    @app.route('/categories/<int:category_id>/questions')
    def questions_from_category(category_id):
        try:
            selection = Question.query.filter(Question.category == category_id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'questions': current_questions,
                'category': category_id,
                'total_questions': len(selection)
            })

        except:
            abort(404)

    """
  QUIZZES
  """

    @app.route('/quizzes', methods=['POST'])
    def post_quizzes():
        try:
            data = request.get_json()
            selected_category = data.get('quiz_category', None)
            previous_questions = data['previous_questions']
            category_id = int(selected_category['id'])

            if category_id == 0:
                if len(previous_questions) > 0:
                    questions = Question.query.filter(Question.id.notin_(previous_questions)).all()
                else:
                    questions = Question.query.all()

            else:
                category = Category.query.get(category_id)

                if len(previous_questions) > 0:
                    questions = Question.query.filter(Question.id.notin_(previous_questions),
                                                      Question.category == category.id).all()
                else:
                    questions = Question.query.filter(Question.category == category.id).all()

            len(questions) - 1
            if len(questions) - 1 > 0:
                question = questions[random.randint(0, len(questions) - 1)].format()
            else:
                return jsonify({
                    'success': True,
                    'question': None
                })

            return jsonify({
                'success': True,
                'question': question
            })

        except:
            abort(500)

    """
  ERROR HANDLERS
  """

    @app.errorhandler(400)
    def bad_request_handler(error):
        return jsonify({
            'success': False,
            'error': 400,
            'message': 'bad request'
        }), 400

    @app.errorhandler(404)
    def not_found_handler(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'page not found'
        }), 404

    @app.errorhandler(405)
    def not_found_handler(error):
        return jsonify({
            'success': False,
            'error': 405,
            'message': 'method not allowed'
        }), 405

    @app.errorhandler(422)
    def unprocessable_handler(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': 'unprocessable'
        }), 422

    @app.errorhandler(500)
    def server_error_handler(error):
        return jsonify({
            'success': False,
            'error': 500,
            'message': 'server error'
        }), 500

    return app
