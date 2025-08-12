import os
from flask import Blueprint, request, jsonify
from app.models.planilla_importacion import PlantillaImportacion
from app.services.import_template_service import create_import_template, delete_import_template, get_all_import_templates, get_import_template_by_id, update_import_template
from werkzeug.utils import secure_filename

import_templates_bp = Blueprint('import_templates', __name__)

UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads', 'excels')
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    
@import_templates_bp.route('/import-templates/upload-excel', methods=['POST'])
def upload_excel():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No se encontró el archivo en la solicitud.'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No se seleccionó ningún archivo.'}), 400

        # Validar extensión
        allowed_extensions = {'xls', 'xlsx'}
        filename = file.filename.lower()

        if not any(filename.endswith(ext) for ext in allowed_extensions):
            return jsonify({'error': 'Archivo no permitido. Solo extensiones .xls y .xlsx son aceptadas.'}), 400

        # Buscar plantilla que coincida con el nombre de archivo
        plantilla = PlantillaImportacion.query.filter(
            (PlantillaImportacion.nombre_archivo_excel == file.filename) | 
            (PlantillaImportacion.nombre_archivo_excel == filename)
        ).first()

        if not plantilla:
            return jsonify({'error': f'No existe plantilla configurada para el archivo "{file.filename}".'}), 404

        # Guardar archivo en la carpeta correspondiente (reemplazar el existente)
        import os
        upload_folder = 'app/static/uploads/excels'
        os.makedirs(upload_folder, exist_ok=True)

        file_path = os.path.join(upload_folder, file.filename)
        file.save(file_path)

        # Actualizar fecha_ultima_lista
        from datetime import datetime
        plantilla.fecha_ultima_lista = datetime.utcnow()
        from app import db
        db.session.commit()

        return jsonify({'message': f'Archivo {file.filename} subido y plantilla actualizada correctamente.'}), 200

    except Exception as e:
        return jsonify({'error': f'Error inesperado: {str(e)}'}), 500