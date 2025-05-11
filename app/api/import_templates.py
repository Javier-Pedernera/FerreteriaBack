from flask import Blueprint, request, jsonify
from app.services.import_template_service import create_import_template, delete_import_template, get_all_import_templates, get_import_template_by_id, update_import_template

import_templates_bp = Blueprint('import_templates', __name__)

@import_templates_bp.route('/import-templates', methods=['POST'])
def create_template():
    try:
        data = request.get_json()
        plantilla = create_import_template(data)
        return jsonify(plantilla.serialize()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
@import_templates_bp.route('/import-templates', methods=['GET'])
def get_templates():
    try:
        templates = get_all_import_templates()
        return jsonify([t.serialize() for t in templates]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@import_templates_bp.route('/import-templates/<int:template_id>', methods=['GET'])
def get_template(template_id):
    try:
        template = get_import_template_by_id(template_id)
        return jsonify(template.serialize()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@import_templates_bp.route('/import-templates/<int:template_id>', methods=['PUT'])
def update_template(template_id):
    try:
        data = request.get_json()
        updated_template = update_import_template(template_id, data)
        return jsonify(updated_template.serialize()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@import_templates_bp.route('/import-templates/<int:template_id>', methods=['DELETE'])
def delete_template(template_id):
    try:
        delete_import_template(template_id)
        return jsonify({'message': 'Plantilla eliminada exitosamente'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400