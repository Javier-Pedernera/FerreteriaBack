from flask import Blueprint, request, jsonify
from app.services.import_template_service import create_import_template

import_templates_bp = Blueprint('import_templates', __name__)

@import_templates_bp.route('/import-templates', methods=['POST'])
def create_template():
    try:
        data = request.get_json()
        plantilla = create_import_template(data)
        return jsonify(plantilla.serialize()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400