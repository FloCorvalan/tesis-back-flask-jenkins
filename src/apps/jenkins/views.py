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

@jenkins.route('/jenkins/info', methods=['GET'])
def update_total_build_service():
    #team_project_id = request.json['team_project_id']
    #source_id = request.json['source_id']
    team_project_id = '625f1e47bffb6a90d59d3e06'
    source_id = '6241fb9a6db9b5f537d59a76'
    # Se obtiene el total de builds de Jenkins y se actualiza en la base de datos
    get_jenkins_info(team_project_id, source_id)
    return {
        'message': 'Successfully extracted data'
    }

@jenkins.route('/jenkins/job-info', methods=['GET'])
def get_participation_job_info_service():
    # Se obtiene la informacion de cada construccion del pipeline
    # para poder despues obtener la participacion de los desarrolladores
    #team_project_id = request.json['team_project_id']
    #source_id = request.json['source_id']
    team_project_id = '625f1e47bffb6a90d59d3e06'
    source_id = '6241fb9a6db9b5f537d59a76'
    # Se obtienen la informacion para calcular la participacion de los desarrolladores
    # (jenkins_job_info)
    get_jenkins_job_info(team_project_id, source_id)
    return {
        'message': 'Successfully extracted data'
    }

@jenkins.route('/jenkins/calculate-participation', methods=['GET'])
def calculate_job_participation_service():
    #team_project_id = request.json['team_project_id']
    #source_id = request.json['source_id']
    team_project_id = '625f1e47bffb6a90d59d3e06'
    source_id = '6241fb9a6db9b5f537d59a76'
    # Se calcula la participacion de los desarrolladores en Jenkins
    calculate_jenkins_participation(team_project_id, source_id)
    return {
        'message': 'Successfully extracted data'
    }

@jenkins.route('/jenkins/calculate-percentages', methods=['GET'])
def calculate_job_percentages_service():
    # Se calculan los porcentajes de participacion de los desarrolladores en Jenkins
    # y se almacenan
    #team_project_id = request.json['team_project_id']
    #source_id = request.json['source_id']
    team_project_id = '625f1e47bffb6a90d59d3e06'
    source_id = '6241fb9a6db9b5f537d59a76'
    # Se calculan los porcentajes de participacion
    calculate_percentages(team_project_id, source_id)
    return {
        'message': 'Successfully extracted data'
    }

@jenkins.route('/jenkins/only-get-team-participation', methods=['GET'])
def only_get_team_participation_service():
    # Se obtiene la participacion de los desarrolladores de un equipo
    # para mostrar los valores
    #team_project_id = request.json['team_project_id']
    #source_id = request.json['source_id']
    team_project_id = '625f1e47bffb6a90d59d3e06'
    source_id = '6241fb9a6db9b5f537d59a76'
    developers = get_team_participation(team_project_id, source_id)
    return developers

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

###################################################################
################### ALL PRODUCTIVITY PROCESS ######################
###################################################################

@jenkins.route('/jenkins/team-prod', methods=['GET'])
def get_jenkins_team_productivity():
    #team_project_id = request.json['team_project_id']
    #source_id = request.json['source_id']
    team_id = '6241fad36d714f635bafbc9f'
    team_project_id = '625f1e47bffb6a90d59d3e06'
    prod = get_prod_info_team(team_id, team_project_id)
    response = json_util.dumps(prod)
    return Response(response, mimetype='application/json')

@jenkins.route('/jenkins/individual-prod', methods=['GET'])
def get_jenkins_individual_productivity():
    #team_project_id = request.json['team_project_id']
    #source_id = request.json['source_id']
    team_id = '6241fad36d714f635bafbc9f'
    team_project_id = '625f1e47bffb6a90d59d3e06'
    prod = get_prod_info_individual(team_id, team_project_id)
    response = json_util.dumps(prod)
    return Response(response, mimetype='application/json')

###################################################################
###################################################################
###################################################################
#------------------------------------------------------------------