if __package__ is None or __package__ == '':
    # uses current directory visibility
    from ...database.database import mongo
else:
    # uses current package visibility
    from database.database import mongo
from bson.objectid import ObjectId

# Se obtiene la informacion de la fuente de informacion de Jenkins 
def get_source_info(source_id):
    source = mongo.db.get_collection('source').find_one({'_id': ObjectId(source_id)})
    ip_port = source['ip_port']
    job = source['name']
    user = source['user']
    token = source['token']
    return ip_port, job, user, token

# Se obtiene el numero de la ultima construccion del pipeline analizada para los registros de 
# process mining
def get_last_build_reg(team_project_id, source_id):
    last_in_bd = mongo.db.get_collection('jenkins_info').find_one({'team_project_id': team_project_id, 'source_id': source_id})
    last_in_bd_exists = mongo.db.get_collection('jenkins_info').find_one({'team_project_id': team_project_id, 'source_id': source_id, 'last_build_reg': {'$exists': True}})
    if last_in_bd_exists != None:
        return last_in_bd['last_build_reg']
    return None

# Se actualiza el case id segun el timestamp porque ocurrio un despliegue exitoso
# y todos los registros que sean posteriores a ese timestamp tendran el nuevo case id
def update_case_id(team_id, team_project_id, timestamp):
    last_case_id = mongo.db.get_collection('team_project').find_one({'_id': ObjectId(team_project_id)})['case_id']
    new_case_id = last_case_id + 1
    mongo.db.get_collection('team_project').update_one({'_id': ObjectId(team_project_id)}, {'$set': {
        'case_id': new_case_id
    }})
    mongo.db.get_collection('registers').update_many({'team_project_id': team_project_id, 'timestamp': {'$gt': timestamp}}, {'$set': {
        'case_id': new_case_id
    }})
    last_case_id_global = mongo.db.get_collection('team').find_one({'_id': ObjectId(team_id)})['last_case_id']
    new_case_id_global = last_case_id_global + 1
    mongo.db.get_collection('team').update_one({'_id': ObjectId(team_id)}, {'$set': {
        'last_case_id': new_case_id_global
    }})
    return new_case_id

# Se actualiza el numero de la ultima ejecucion del pipeline analizada
def update_last_build_number(team_project_id, build_number, source_id):
    mongo.db.get_collection('jenkins_info').update_one({'team_project_id': team_project_id, 'source_id': source_id}, {'$set': {
        'last_build_reg': build_number
    }})

# Se obtiene el case id actual para un proyecto
def get_actual_case_id(team_project_id):
    team_project = mongo.db.get_collection('team_project').find_one({'_id': ObjectId(team_project_id)})
    case_id = team_project['case_id']
    return case_id

# Se guarda un registro para process mining
def save_register(team_project_id, case_id, activity, timestamp, username, buildnumber):
    mongo.db.get_collection('registers').insert_one({
                    'team_project_id': team_project_id,
                    'case_id': case_id,
                    'activity': activity, 
                    'timestamp': timestamp,
                    'resource': 'jenkins',
                    'tool': 'jenkins',
                    'userName': username,
                    'build_number': buildnumber
                })

# Se actualiza el numero total de construcciones del pipeline
def update_total_build(team_project_id, source_id, total_build):
    res = mongo.db.get_collection('jenkins_info').find_one({'team_project_id': team_project_id, 'source_id': source_id})
    if res == None:
        mongo.db.get_collection('jenkins_info').insert_one({
            'team_project_id': team_project_id, 
            'source_id': source_id,
            'total_build': total_build, 
            'last_build_part': 0
        })
    else:
        mongo.db.get_collection('jenkins_info').update_one({'team_project_id': team_project_id, 'source_id': source_id}, {'$set':{
            'total_build': total_build
        }})

# Se obtiene el numero de la ejecucion del pipeline que se analizo ultimo para la participacion
def get_last_build_part(team_project_id, source_id):
    team = mongo.db.get_collection('jenkins_info').find_one({'team_project_id': team_project_id, 'source_id': source_id})
    last_in_bd = team['last_build_part']
    total_build = team['total_build']
    return last_in_bd, total_build

# Se guarda un documento con la informacion de una ejecucion del pipeline para luego
# extraer la participacion de esos documentos
def insert_jenkins_job_info(team_project_id, job, number, username, status, source_id, timestamp):
    mongo.db.get_collection('jenkins_job_info').insert_one({
            'team_project_id': team_project_id,
            'job_name': job,
            'build_number': number,
            'username': username,
            'result': status, 
            'source_id': source_id, 
            'timestamp': timestamp
        })

# Se actualiza el numero de ejecucion del pipeline analizado ultimo para la participacion
def update_last_build_part(team_project_id, source_id, number):
    mongo.db.get_collection('jenkins_info').update_one({'team_project_id': team_project_id, 'source_id': source_id}, {'$set': {
            'last_build_part': number
        }})

# Se calcula la participacion de los desarrolladores en Jenkins
def calculate_jenkins_participation_db(team_project_id, source_id):
    total = mongo.db.get_collection('jenkins_job_info').aggregate([
        {
            '$match': {
                'team_project_id': team_project_id,
                'source_id': source_id
            }
        },
        {
            '$group': {
                '_id': '$username',
                'count': {'$sum':1}
            }
        },
        {
            '$project': {
                'username': '$_id.username',
                'count': '$count'
            }
        }
    ])
    for doc in total:
        res = mongo.db.get_collection('jenkins_participation').find_one({'team_project_id': team_project_id, 'source_id': source_id, 'username': doc['_id']})
        if res == None:
            mongo.db.get_collection('jenkins_participation').insert_one({
                'team_project_id': team_project_id, 
                'username': doc['_id'],
                'total_build': doc['count'], 
                'success_build': 0,
                'failure_build': 0,
                'source_id': source_id
            })
        else:
            mongo.db.get_collection('jenkins_participation').update_one({'team_project_id': team_project_id, 'source_id': source_id, 'username': doc['_id']}, {'$set': {
                'total_build': doc['count']
            }})

    success = mongo.db.get_collection('jenkins_job_info').aggregate([
        {
            '$match': {
                'team_project_id': team_project_id,
                'source_id': source_id,
                'result': 'SUCCESS'
            }
        },
        {
            '$group': {
                '_id': '$username',
                'count': {'$sum':1}
            }
        },
        {
            '$project': {
                'username': '$_id.username',
                'count': '$count'
            }
        }
    ])

    for doc in success:
        mongo.db.get_collection('jenkins_participation').update_one({'team_project_id': team_project_id, 'source_id': source_id, 'username': doc['_id']}, {'$set': {
                'success_build': doc['count']
            }})

    failure = mongo.db.get_collection('jenkins_job_info').aggregate([
        {
            '$match': {
                'team_project_id': team_project_id,
                'source_id': source_id,
                'result': 'FAILURE'
            }
        },
        {
            '$group': {
                '_id': '$username',
                'count': {'$sum':1}
            }
        },
        {
            '$project': {
                'username': '$_id.username',
                'count': '$count'
            }
        }
    ])

    for doc in failure:
        mongo.db.get_collection('jenkins_participation').update_one({'team_project_id': team_project_id, 'source_id': source_id, 'username': doc['_id']}, {'$set': {
                'failure_build': doc['count']
            }})

# Se calculan los porcentajes de participacion de los desarrolladores en Jenkins
def calculate_percentages_db(team_project_id, source_id):
    job = mongo.db.get_collection('jenkins_info').find_one({'team_project_id': team_project_id, 'source_id': source_id})
    total_build = job['total_build']
    developers = mongo.db.get_collection('jenkins_participation').find({'team_project_id': team_project_id, 'source_id': source_id})
    for developer in developers:
        developer_total = developer['total_build']
        total_per = int(developer_total/total_build * 100)
        success_per = int(developer['success_build']/developer_total * 100)
        failure_per = int(developer['failure_build']/developer_total * 100)
        mongo.db.get_collection('jenkins_participation').update_one({'team_project_id': team_project_id, 'source_id': source_id, 'username': developer['username']}, {'$set': {
           'total_per': total_per, 
           'success_per': success_per, 
           'failure_per': failure_per 
        }})

# Se obtiene la participacion de los desarrolladores en Jenkins
def get_team_participation_db(team_project_id, source_id):
    developers = mongo.db.get_collection('jenkins_participation').find({'team_project_id': team_project_id, 'source_id': source_id})
    return developers

# Se obtiene el numero total de construcciones del pipeline
def get_total_builds(team_project_id, source_id):
    total = mongo.db.get_collection('jenkins_info').find_one({'team_project_id': team_project_id, 'source_id': source_id})
    if total != None:
        return total['total_build']
