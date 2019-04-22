from uuid import UUID
from flask import Flask, jsonify, request, make_response, g
from db_service import DbService
from messaging_service import MessagingService

app = Flask(__name__)
db_service = DbService()
messaging_service = MessagingService()

def create_error_response(msg, code = 400):
    message = jsonify({ 'message': msg })
    return make_response(message, code)

def empty():
    return jsonify({})

def index():
    return jsonify(success=True)

def is_uuid(val):
    try:
        UUID(val, version=4)
        return True
    except ValueError:
        return False

@app.route('/photos/pending')
def get_photos_pending():
    try:
        results = db_service.get_by_status('pending')
        return jsonify(results)
    except Exception as ex:
        return create_error_response('Internal Server Error: {}'.format(str(ex)), 500)

@app.route('/photos/process', methods = ['POST'])
def process_photo():
    input = request.get_json(force=True)
    response = None
    response_payload = {
        'accepted': [],
        'rejected': []
    }

    try:
        if isinstance(input, type([])):
            for uuid in input:
                if not is_uuid(uuid):
                    response_payload['rejected'].append(uuid)
                else:
                    messaging_service.push(uuid)
                    response_payload['accepted'].append(uuid)
            if len(response_payload['rejected']) == len(input) and len(input) > 0:
                response = create_error_response('None of the provided inputs could be parsed as a UUID')
            else:
                response = make_response(jsonify(response_payload), 201)
        else:
            response = create_error_response('Invalid payload format', 406)
    except Exception as ex:
        response = create_error_response('Internal Server Error: {}'.format(str(ex)), 500)

    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
