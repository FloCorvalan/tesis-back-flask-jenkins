from flask import request, jsonify, Response, Blueprint
from bson import json_util
from bson.objectid import ObjectId
from .methods import *

jenkins = Blueprint('jenkins', __name__)

###################################################################
########################## REGISTERS ##############################
###################################################################

@jenkins.route('/jenkins', methods=['POST'])
def get_registers_service():
    team_id = request.json['team_id']
    team_project_id = request.json['team_project_id']
    source_id = request.json['source_id']
    #team_id = '6241fad36d714f635bafbc9f'
    #team_project_id = '625f1e47bffb6a90d59d3e06'
    #source_id = '6241fb9a6db9b5f537d59a76'
    # Se obtienen los registros (para process mining) desde Jenkins
    get_jenkins_data(team_id, team_project_id, source_id)
    return {
        'message': 'Successfully extracted data'
    }

###################################################################
###################################################################
###################################################################


###################################################################
################### ALL PARTICIPATION PROCESS #####################
###################################################################

@jenkins.route('/jenkins/participation', methods=['POST'])
def get_team_participation_service():
    # Se obtiene la participacion de los desarrolladores de un equipo
    # para mostrar los valores
    team_project_id = request.json['team_project_id']
    source_id = request.json['source_id']
    #team_project_id = '625f1e47bffb6a90d59d3e06'
    #source_id = '6241fb9a6db9b5f537d59a76'

    # Se obtiene el total de builds de Jenkins y se actualiza en la base de datos
    get_jenkins_info(team_project_id, source_id)

    # Se obtienen la informacion para calcular la participacion de los desarrolladores
    # (jenkins_job_info)
    get_jenkins_job_info(team_project_id, source_id)

    # Se calcula la participacion de los desarrolladores en Jenkins
    calculate_jenkins_participation(team_project_id, source_id)

    # Se calculan los porcentajes de participacion
    calculate_percentages(team_project_id, source_id)

    # Se obtiene la participacion de los desarrolladores para mostrarla
    developers = get_team_participation(team_project_id, source_id)
    return developers

@jenkins.route('/jenkins/stages', methods=['POST'])
def get_stages_service():
    # Se obtiene la participacion de los desarrolladores de un equipo
    # para mostrar los valores
    team_project_id = request.json['team_project_id']
    source_id = request.json['source_id']

    stages = get_stages_info(team_project_id, source_id)

    response = json_util.dumps(stages)
    return Response(response, mimetype='application/json')

###################################################################
###################################################################
###################################################################