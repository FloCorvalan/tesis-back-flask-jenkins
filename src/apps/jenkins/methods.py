import requests
import numpy as np
import json
from bson import json_util
from datetime import datetime
from flask import Response
from .db_methods import *

###################################
########## REGISTERS ##############
###################################

############################ ACTIVIDADES ############################
TEST = ["mvn test", "gradle test"]
CODE_ANALYSIS = ["./gradlew sonarqube", "mvn org.sonarsource", "sonar:sonar", "gradle sonarqube"]
BUILD = ["mvn package", "mvn clean package","gradle build", "gradlew build"]
BUILD_IMG = ["docker-compose build", "docker build"]
DEPLOY = ["docker run", "kubectl apply", "mvn deploy", "docker-compose up"]

DIC = {
    "TEST":"PRUEBAS",
    "CODE_ANALYSIS":"ANALISIS",
    "BUILD":"CONSTRUIR",
    "BUILD_IMG":"CONSTRUIR_IMAGEN",
    "DEPLOY":"DESPLIEGUE",
    "PIPELINE":"EJECUCION_PIPELINE"
}

#####################################################################

# Se obtiene la infomacion de una construccion del pipeline
def get_lines(buildNumber, source_id):
    ip_port, job, user, token = get_source_info(source_id)

    base_url = "http://" + user + ":" + token + "@" + ip_port + "/job/" + job

    console_output_url = base_url + "/" + str(buildNumber) + "/timestamps/?time=yyyy-MM-dd%HH:mm:ss&appendLog"
    res = requests.get(console_output_url)
    res_arr = np.array(res.text.split("\n"))
    info_url = base_url + "/" + str(buildNumber) + "/api/json"
    info_res = requests.get(info_url)
    info = json.loads(info_res.text)
    status = info['result']
    timestamp = (info['timestamp'] // 1000)
    try:
        userName = info['actions'][0]['causes'][0]['userName']
    except:
        userName = info['actions'][0]['causes'][0]['shortDescription'].split(' ')[-1]
    return res_arr, status, userName, timestamp

# Se obtiene una lista de los identificadores de las ejecuciones del pipeline que se deben revisar
# (numero de ejecucion)
def get_build_numbers(team_project_id, source_id):
    ip_port, job, user, token = get_source_info(source_id)

    base_url = "http://" + user + ":" + token + "@" + ip_port + "/job/" + job

    lastBuildNumber = requests.get(base_url + "/lastBuild/buildNumber")
    # Consultar a la bd por el ultimo build analizado
    last_in_bd = get_last_build_reg(team_project_id, source_id)
    if last_in_bd == None:
        last_in_bd = 1
    else: 
        last_in_bd += 1 # Porque comienza con el siguiente
    build_numbers = range(last_in_bd, int(lastBuildNumber.text) + 1)
    return build_numbers

# Se analiza una linea de la salida console output de una ejecucion del pipeline
# buscando si existen coincidencias con los comandos definidos arriba para cada actividad
def analize_one_line(line):
    # Se analiza el contenido de una linea y se entrega la actividad y el timestamp
    if any(word in line for word in TEST):
        return DIC["TEST"], line.split(" ")[0]
    if any(word in line for word in CODE_ANALYSIS):
        return DIC["CODE_ANALYSIS"], line.split(" ")[0]
    if any(word in line for word in BUILD):
        return DIC["BUILD"], line.split(" ")[0]
    if any(word in line for word in BUILD_IMG):
        return DIC["BUILD_IMG"], line.split(" ")[0]
    if any(word in line for word in DEPLOY):
        return DIC["DEPLOY"], line.split(" ")[0]
    return None, None

# Se analizan las lineas de la salida console output de una ejecucion del pipeline
# y se agregan registros para process mining si se encuentran coincidencias en los comandos de 
# las actividades
# (el despliegue se registra solo si es exitoso)
def analize_lines(team_id, team_project_id, lines, status, userName, timestamp, buildNumber):
    i = 0
    case_id = get_actual_case_id(team_project_id)

    save_register(team_project_id, case_id, DIC['PIPELINE'], timestamp, userName, buildNumber)

    while i < len(lines) - 1:
        if lines[i].find(" sh") != -1:
            act, time = analize_one_line(lines[i+1])
            if act != None:
                if time != '':
                    time = datetime.strptime(time, "%Y-%m-%d%%%H:%M:%S").timestamp()
                # Guardar registro en bd
                if act != DIC["DEPLOY"]:
                    save_register(team_project_id, case_id, act, time, userName, buildNumber)
                if act == DIC["DEPLOY"] and status == "SUCCESS":
                    save_register(team_project_id, case_id, act, time, userName, buildNumber)
                    # Actualizar case_id y cambiar case_id de los registros con timestamp posterior
                    case_id = update_case_id(team_id, team_project_id, time)
        i += 1

# Todo el proceso que obtiene los registros para process mining
def get_jenkins_data(team_id, team_project_id, source_id):
    # Se obtienen los build numbers de los console output que no han sido analizados
    build_numbers = get_build_numbers(team_project_id, source_id)
    # Por cada build number se generan registros
    for number in build_numbers:
        # Se generan registros (analisis y guardar en bd)
        lines, status, userName, timestamp = get_lines(number, source_id)
        analize_lines(team_id, team_project_id, lines, status, userName, timestamp, number)
        # Se actualiza el last_build_number analizado
        update_last_build_number(team_project_id, number, source_id)

###################################
########## PARTICIPATION ##########
###################################

# Se obtiene la informacion del pipeline de Jenkins asociado a un proyecto y segun su id
# y se actualiza en la bd el numero total de construcciones hasta el momento
def get_jenkins_info(team_project_id, source_id):
    ip_port, job, user, token = get_source_info(source_id)
    
    base_url = "http://" + user + ":" + token + "@" + ip_port + "/job/" + job

    total_build_res = requests.get(base_url + "/lastBuild/buildNumber")
    total_build = int(total_build_res.text)
    
    update_total_build(team_project_id, source_id, total_build)

# Se obtiene la informacion de cada ejecucion del pipeline 
# (para identificar como participaron en las ejecuciones los desarrolladores)
# (auto) = se ha iniciado el pipeline automaticamente mediante el webhook de GitHub
def get_jenkins_job_info(team_project_id, source_id):
    ip_port, job, user, token = get_source_info(source_id)
    
    base_url = "http://" + user + ":" + token + "@" + ip_port + "/job/" + job

    last_in_bd, total_build = get_last_build_part(team_project_id, source_id)
    last_in_bd += 1 # Porque comienza con el siguiente

    build_numbers = range(last_in_bd, total_build + 1)
    for number in build_numbers:
        info_url = base_url + "/" + str(number) + "/api/json"
        info_res = requests.get(info_url)
        info = json.loads(info_res.text)
        status = info['result']
        try:
            userName = info['actions'][0]['causes'][0]['userName']
        except:
            userName = info['actions'][0]['causes'][0]['shortDescription'].split(' ')[-1] + ' (auto)'
        timestamp = (info['timestamp'] // 1000)
        insert_jenkins_job_info(team_project_id, job, number, userName, status, source_id, timestamp)
        update_last_build_part(team_project_id, source_id, number)

# Se calcula la participacion en Jenkins segun la informacion registrada de cada ejecucion del pipeline
# (arriba)
def calculate_jenkins_participation(team_project_id, source_id):
    calculate_jenkins_participation_db(team_project_id, source_id)

# Se calculan los porcentajes de participacion por desarrollador
def calculate_percentages(team_project_id, source_id):
    calculate_percentages_db(team_project_id, source_id)

# Se obtine la participacion de los desarrolladores junto con el total de construcciones del pipeline
def get_team_participation(team_project_id, source_id):
    developers = get_team_participation_db(team_project_id, source_id)
    total_builds = get_total_builds(team_project_id, source_id)
    participation = {
        'developers': developers, 
        'total_builds': total_builds
    }

    response = json_util.dumps(participation)
    return Response(response, mimetype='application/json')

# Se obtiene la informacion de los stages (nombres y cantidad) de cada ejecucion del pipeline
def get_stages_info(team_project_id, source_id):
    ip_port, job, user, token = get_source_info(source_id)
    base_url = "http://" + user + ":" + token + "@" + ip_port + "/job/" + job
    last_in_bd, total_build = get_last_build_part(team_project_id, source_id)
    build_numbers = range(1, total_build + 1)
    stages_send = {}
    for number in build_numbers:
        info_url = base_url + "/" + str(number) + "/wfapi/describe"
        info_res = requests.get(info_url)
        info = json.loads(info_res.text)
        stages_inner = []
        stages = info['stages']
        for stage in stages:
            stages_inner.append(stage['name'])
        stages_send[number] = {
            'stages_names': stages_inner,
            'count': len(stages_inner)
        }
        stages_inner = []
    return stages_send

    