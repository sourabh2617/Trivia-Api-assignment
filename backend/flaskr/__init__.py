from flask import Flask, request, abort, jsonify
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

    # CORS Headers
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PUT,POST,DELETE,OPTIONS')
        return response

    # Create an endpoint to handle GET requests for all available categories.
    @app.route('/categories', methods=['GET'])
    def get_categories():
        selection = Category.query.order_by(Category.id).all()
        current_categories = paginate_questions(request, selection)

        if len(current_categories) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'categories': {cat.id: cat.type for cat in selection}
        })

    # Create an endpoint to handle GET requests for questions,
    # including pagination (every 10 questions).
    @app.route("/questions", methods=['GET'])
    def get_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        if len(current_questions) == 0:
            abort(404)

        # This endpoint should return a list of questions,
        # number of total questions, current category, categories.
        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection),
            'current_category': [],
            'categories': [cat.type for cat in Category.query.all()],
        }), 200

    # Create an endpoint to DELETE question using a question ID.
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)
            return jsonify({
                'success': True,
                'deleted': question_id,
                'questions': current_questions,
                'total_questions': len(selection)
            })

        except Exception:
            abort(422)

    # Create an endpoint to POST a new question
    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()

        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)
        search = body.get('searchTerm', None)

        try:
            if search:
                questions = Question.query.filter(
                    Question.question.ilike(f'%{search}%')
                ).all()

                current_questions = [question.format()
                                     for question in questions]
                return jsonify({
                    'success': True,
                    'questions': current_questions,
                    'total_questions': len(current_questions),
                })

            else:
                question = Question(
                    question=new_question,
                    answer=new_answer,
                    category=new_category,
                    difficulty=new_difficulty
                )
                question.insert()

                selection = Question.query.order_by(Question.id).all()
                current_questions = paginate_questions(request, selection)

                return jsonify({
                    'success': True,
                    'questions': current_questions,
                    'total_questions': len(Question.query.all())
                })
        except Exception:
            abort(422)

    @app.route('/categories/<int:cat_id>/questions', methods=['GET'])
    def get_questions_by_category(cat_id):
        cat_id = cat_id + 1
        category = Category.query.filter(
            Category.id == cat_id).first()

        selection = Question.query.order_by(Question.id).filter(
            Question.category == cat_id).all()
        current_questions = paginate_questions(request, selection)

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection),
            'categories': [cat.type for cat in Category.query.all()],
            'current_category': category.format()
        })

    # Create a POST endpoint to get questions to play the quiz.
    @app.route('/quizzes', methods=['POST'])
    def get_quizzes():
        # This endpoint should take category and previous question parameters
        try:
            body = request.get_json()
            previous_questions = body.get('previous_questions', None)
            quiz_category = body.get('quiz_category', None)
            category_id = quiz_category['id']

            if category_id == 0:
                questions = Question.query.filter(
                    Question.id.notin_(previous_questions)).all()
            else:
                questions = Question.query.filter(
                    Question.id.notin_(previous_questions),
                    Question.category == category_id).all()
            question = None
            if(questions):
                question = random.choice(questions)

            return jsonify({
                'success': True,
                'question': question.format()
            })

        except Exception:
            abort(422)

    # error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Resource Not Found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "Not Processable"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Bad Request"
        }), 400

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "Internal Server Error"
        }), 500

    return app