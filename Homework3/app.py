from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')
db = client['loan_db']
applications = db['applications']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/apply', methods=['POST'])
def apply():
    data = request.json
    if not data.get('name') or not data.get('zipcode') or not data.get('address'):
        return jsonify({'error': 'Name, zipcode, and address are required'}), 400

    application = {
        "name": data['name'],
        "zipcode": data['zipcode'],
        "address": data['address'],
        "status": "received",
        "notes": [],
        "subphases": {},
        "loan_terms": [],
        "rejection_reason": None
    }
    result = applications.insert_one(application)
    return jsonify({'application_id': str(result.inserted_id)})

@app.route('/api/status/<application_id>', methods=['GET'])
def check_status(application_id):
    app_data = applications.find_one({'_id': ObjectId(application_id)})
    if not app_data:
        return jsonify({'status': 'not found'}), 404
    return jsonify({'status': app_data['status']})

@app.route('/api/status/<application_id>', methods=['PUT'])
def change_status(application_id):
    data = request.json
    new_status = data.get('status')

    if new_status not in ['received', 'processing', 'accepted', 'rejected']:
        return jsonify({'error': 'Invalid status'}), 400

    result = applications.update_one(
        {'_id': ObjectId(application_id)},
        {'$set': {'status': new_status}}
    )

    if result.matched_count == 0:
        return jsonify({'error': 'Application not found'}), 404

    return jsonify({'message': 'Status updated successfully'})

@app.route('/api/note/<application_id>', methods=['POST'])
def add_note(application_id):
    data = request.json
    note = data.get('note')

    if not note:
        return jsonify({'error': 'Note text is required'}), 400

    result = applications.update_one(
        {'_id': ObjectId(application_id)},
        {'$push': {'notes': note}}
    )

    if result.matched_count == 0:
        return jsonify({'error': 'Application not found'}), 404

    return jsonify({'message': 'Note added successfully'})

@app.route('/api/notes/<application_id>', methods=['GET'])
def view_notes(application_id):
    app_data = applications.find_one(
        {'_id': ObjectId(application_id)},
        {
            'notes': 1,
            'rejection_reason': 1,
            'loan_terms': 1,
            'subphases': 1,
            '_id': 0
        }
    )
    if not app_data:
        return jsonify({'error': 'Application not found'}), 404

    combined_notes = []

    # 1. Add general notes
    combined_notes.extend(app_data.get('notes', []))

    # 2. Add subphase messages
    subphases = app_data.get('subphases', {})
    for subphase, messages in subphases.items():
        for msg in messages:
            combined_notes.append(f"[Subphase: {subphase}] {msg}")

    # 3. Add loan terms
    for term in app_data.get('loan_terms', []):
        combined_notes.append(f"[Loan Term] {term}")

    # 4. Add rejection reason if present
    if app_data.get('rejection_reason'):
        combined_notes.append(f"[Rejection Reason] {app_data['rejection_reason']}")

    return jsonify({'notes': combined_notes})


@app.route('/api/subphase/<application_id>', methods=['POST'])
def add_subphase(application_id):
    data = request.json
    subphase = data.get('subphase')
    message = data.get('message')

    if not subphase or not message:
        return jsonify({'error': 'Subphase and message are required'}), 400

    result = applications.update_one(
        {'_id': ObjectId(application_id)},
        {'$push': {f'subphases.{subphase}': message}}
    )

    if result.matched_count == 0:
        return jsonify({'error': 'Application not found'}), 404
    return jsonify({'message': f'Message added to subphase {subphase}'})

@app.route('/api/reject/<application_id>', methods=['PUT'])
def reject_application(application_id):
    data = request.json
    reason = data.get('reason')

    if not reason:
        return jsonify({'error': 'Rejection reason is required'}), 400

    result = applications.update_one(
        {'_id': ObjectId(application_id)},
        {'$set': {'status': 'rejected', 'rejection_reason': reason}}
    )
    if result.matched_count == 0:
        return jsonify({'error': 'Application not found'}), 404
    return jsonify({'message': 'Application rejected and reason saved'})

@app.route('/api/loan_terms/<application_id>', methods=['POST'])
def add_loan_term(application_id):
    data = request.json
    term = data.get('term')

    if not term:
        return jsonify({'error': 'Loan term is required'}), 400

    app_data = applications.find_one({'_id': ObjectId(application_id)})
    if not app_data:
        return jsonify({'error': 'Application not found'}), 404

    if app_data['status'] != 'accepted':
        return jsonify({'error': 'Loan terms can only be added to accepted applications'}), 400

    applications.update_one(
        {'_id': ObjectId(application_id)},
        {'$push': {'loan_terms': term}}
    )
    return jsonify({'message': 'Loan term added successfully'})

@app.route('/api/application/<application_id>', methods=['GET'])
def view_application(application_id):
    try:
        app_data = applications.find_one({'_id': ObjectId(application_id)}, {'_id': 0})
        if not app_data:
            return jsonify({'error': 'Application not found'}), 404
        return jsonify(app_data)
    except:
        return jsonify({'error': 'Invalid application ID format'}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)