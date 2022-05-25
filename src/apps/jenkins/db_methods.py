if __package__ is None or __package__ == '':
    # uses current directory visibility
    from ...database.database import mongo
else:
    # uses current package visibility
    from database.database import mongo
from bson.objectid import ObjectId

def get_source_info(source_id):
    source = mongo.db.get_collection('source').find_one({'_id': ObjectId(source_id)})
    ip_port = source['ip_port']
    job = source['name']
    user = source['user']
    token = source['token']
    return ip_port, job, user, token

def get_last_build_reg(team_project_id, source_id):
    last_in_bd = mongo.db.get_collection('jenkins_info').find_one({'team_project_id': team_project_id, 'source_id': source_id})
    last_in_bd_exists = mongo.db.get_collection('jenkins_info').find_one({'team_project_id': team_project_id, 'source_id': source_id, 'last_build_reg': {'$exists': True}})
    if last_in_bd_exists != None:
        return last_in_bd['last_build_reg']
    return None

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

def update_last_build_number(team_project_id, build_number, source_id):
    mongo.db.get_collection('jenkins_info').update_one({'team_project_id': team_project_id, 'source_id': source_id}, {'$set': {
        'last_build_reg': build_number
    }})

def get_actual_case_id(team_project_id):
    team_project = mongo.db.get_collection('team_project').find_one({'_id': ObjectId(team_project_id)})
    case_id = team_project['case_id']
    return case_id

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

def get_last_build_part(team_project_id, source_id):
    team = mongo.db.get_collection('jenkins_info').find_one({'team_project_id': team_project_id, 'source_id': source_id})
    last_in_bd = team['last_build_part']
    total_build = team['total_build']
    return last_in_bd, total_build

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

def update_last_build_part(team_project_id, source_id, number):
    mongo.db.get_collection('jenkins_info').update_one({'team_project_id': team_project_id, 'source_id': source_id}, {'$set': {
            'last_build_part': number
        }})

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
    #print(total)
    for doc in total:
        #print(doc)
        res = mongo.db.get_collection('jenkins_participation').find_one({'team_project_id': team_project_id, 'source_id': source_id, 'username': doc['_id']})
        #print(res)
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
        #print(doc)
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
        #print(doc)
        mongo.db.get_collection('jenkins_participation').update_one({'team_project_id': team_project_id, 'source_id': source_id, 'username': doc['_id']}, {'$set': {
                'failure_build': doc['count']
            }})

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

def translate_name(db_developers, part_name):
    for dev in db_developers:
        if(dev['jenkins'] == part_name):
            return dev['name'], dev
    return None, None

def find_team_developers(team_project_id):
    teams = mongo.db.get_collection('team').find({'projects': {'$exists': True}, 'developers': {'$exists': True}})
    for team in teams:
        projects = team['projects']
        for p in projects:
            if(p == team_project_id):
                return team['developers']
    return None

def get_team_participation_db_2(team_project_id, source_id):
    developers = mongo.db.get_collection('jenkins_participation').find({'team_project_id': team_project_id, 'source_id': source_id})
    developers_db = find_team_developers(team_project_id)
    print(developers_db)
    developers_db_names = []
    if(developers_db != None):
        for dev in developers_db:
            developer = mongo.db.get_collection('developer').find_one({'_id': ObjectId(dev)})
            developers_db_names.append(developer)
    developers_send = []
    for dev in developers:
        name, developer = translate_name(developers_db_names, dev['username'])
        if(name != None):
            developers_db_names.remove(developer)
            dev['username'] = name
        developers_send.append(dev)
    for dev in developers_db_names:
        name = dev['name']
        developers_send.append({
            'username': name, 
            'success_per': 0,
            'failure_per': 0, 
            'total_per': 0
        })
    return developers_send

def get_team_participation_db(team_project_id, source_id):
    developers = mongo.db.get_collection('jenkins_participation').find({'team_project_id': team_project_id, 'source_id': source_id})
    return developers

def get_total_builds(team_project_id, source_id):
    total = mongo.db.get_collection('jenkins_info').find_one({'team_project_id': team_project_id, 'source_id': source_id})
    if total != None:
        return total['total_build']

#################################################
############### PRODUCTIVITY ####################
#################################################

def get_prod_docs_team(team_project_id):
    docs = mongo.db.get_collection('jenkins_job_info').find({'team_project_id': team_project_id, 'result': 'SUCCESS'})
    if docs.count() != 0:
        return docs
    return None

### individual
def get_developers(team_id):
    team = mongo.db.get_collection('team').find_one({'_id': ObjectId(team_id)})
    developers = team['developers']
    return developers

def get_developer_names(dev_id):
    dev = mongo.db.get_collection('developer').find_one({'_id': ObjectId(dev_id)})
    jenkins_name = dev['jenkins']
    name = dev['name']
    return jenkins_name, name

def get_prod_docs(team_project_id):
    docs = mongo.db.get_collection('jenkins_job_info').find({'team_project_id': team_project_id})
    return docs

def get_prod_docs_by_developer(team_project_id, developer):
    docs = mongo.db.get_collection('jenkins_job_info').find({'team_project_id': team_project_id, 'username': developer, 'result': 'SUCCESS'})
    if docs.count() != 0:
        return docs
    return None