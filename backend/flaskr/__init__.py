import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_content(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    books = [book.format() for book in selection]
    current_books = books[start:end]

    return current_books


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    CORS(app)

    @ app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    @app.route('/categories')
    def get_categories():
        categories = Category.query.all()
        current_categories = paginate_content(request, categories)
        return jsonify({
            'success': True,
            'categories': current_categories,

        })

    @app.route('/questions', methods=['GET'])
    def get_questions():
        questions = Question.query.order_by(Question.id.desc()).all()
        current_questions = paginate_content(request, questions)

        return jsonify({
            "questions": current_questions,
            'categories': [category.format() for category in Category.query.all()],
            'current_category': (Category.query.order_by(Category.id).first()).format(),
            "total_questions": len(questions),
        })

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        question = Question.query.filter(
            Question.id == question_id).one_or_none()

        if question is None:
            abort(404)

        question.delete()
        selection = Question.query.order_by(Question.id.desc()).all()
        current_questions = paginate_content(request, selection)

        return jsonify({
            "success": True,
            "deleted": question_id,
            "questions": current_questions,
            "total_questions": len(selection)
        })

    @app.route('/questions', methods=['POST'])
    def create_new_question():
        question = request.get_json()['question']
        answer = request.get_json()['answer']
        category = request.get_json()['category']
        difficulty = request.get_json()['difficulty']

        new_question = Question(
            question=question, answer=answer, category=category, difficulty=difficulty)
        new_question.insert()
        selection = Question.query.order_by(Question.id.desc()).all()
        current_questions = paginate_content(request, selection)

        return jsonify({
            "success": True,
            "created": new_question.id,
            "questions": current_questions,
            "total_questions": len(selection)
        })

    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        search_term = request.get_json()['searchTerm']
        selection = Question.query.filter(
            Question.question.ilike(f'%{search_term}%')).all()
        current_questions = paginate_content(request, selection)

        return jsonify({
            "success": True,
            "questions": current_questions,
            "total_questions": len(selection)
        })

    @app.route('/categories/<int:category_id>/questions')
    def get_questions_by_category(category_id):
        selection = Question.query.filter(
            Question.category == category_id).all()
        current_questions = paginate_content(request, selection)

        return jsonify({
            "success": True,
            "questions": current_questions,
            "current_category": (Category.query.filter(Category.id == category_id).first()).format(),
            "total_questions": len(selection)
        })

    @app.route('/quizzes', methods=['POST'])
    def quizzes():
        category = request.get_json()['quiz_category']['id']
        previous_questions = request.get_json()['previous_questions']
        selection = Question.query.filter(
            Question.category == category).filter(
                Question.id.notin_(previous_questions)).all()
        current_question = paginate_content(request, selection)

        return jsonify({
            "success": True,
            "question": current_question[0] if len(current_question) > 0 else None
        })

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "Unprocessable"
        }), 422

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "Server error"
        }), 500

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Bad request"
        }), 400

    return app
