from json import loads

def test_participation_jenkins(test_client):
    '''HU5 - Escenario 1 parte 3'
    'Dado que existe al menos un proyecto asociado al equipo de desarrollo y está registrada la fuente de información de Jira'
    'Cuando el líder de proyectos accede al dashboard del equipo de desarrollo'
    'Entonces se genera el dashboard a partir de los datos extraídos de las fuentes de información registradas'''

    '''HU12 - Escenario 1 parte 2'
    'Dado que existe al menos un proyecto asociado al equipo de desarrollo y está registrada la fuente de información de Jira'
    'Cuando el líder de proyectos accede al dashboard del equipo de desarrollo'
    'Y se genera el dashboard a partir de los datos extraídos de las fuentes de información registradas'
    'Entonces el sistema entrega la participación general de los desarrolladores en Jira, y la participación de los desarrolladores en Jenkins y GitHub por proyecto'''


    team_project_id = '629f70971785c7fd81349a19'
    source_id = '629f70971785c7fd81349a1a'

    client, mongo = test_client

    response = client.post('/jenkins/participation', json={
        'team_project_id': team_project_id, 
        'source_id': source_id
    })

    data_str = response.data.decode('utf8')

    data = loads(data_str)

    assert 'developers' in data.keys()
    assert len(data['developers']) == 3
    
    i = 0
    while i < len(data['developers']):
        if data['developers'][i]['_id']['$oid'] == '629f709f1785c7fd81349a3f':
            assert data['developers'][i]['username'] == 'fcorvalanl (auto)'
            assert data['developers'][i]['total_build'] == 4
            assert data['developers'][i]['success_build'] == 4
            assert data['developers'][i]['failure_build'] == 0
            assert data['developers'][i]['failure_per'] == 0
            assert data['developers'][i]['success_per'] == 100
            assert data['developers'][i]['total_per'] == 57
        elif data['developers'][i]['_id']['$oid'] == '629f709f1785c7fd81349a40':
            assert data['developers'][i]['username'] == 'FloCorvalan (auto)'
            assert data['developers'][i]['total_build'] == 2
            assert data['developers'][i]['success_build'] == 2
            assert data['developers'][i]['failure_build'] == 0
            assert data['developers'][i]['failure_per'] == 0
            assert data['developers'][i]['success_per'] == 100
            assert data['developers'][i]['total_per'] == 28
        elif data['developers'][i]['_id']['$oid'] == '629f709f1785c7fd81349a41':
            assert data['developers'][i]['username'] == 'admin'
            assert data['developers'][i]['total_build'] == 1
            assert data['developers'][i]['success_build'] == 1
            assert data['developers'][i]['failure_build'] == 0
            assert data['developers'][i]['failure_per'] == 0
            assert data['developers'][i]['success_per'] == 100
            assert data['developers'][i]['total_per'] == 14
        i += 1

    assert 'total_builds' in data.keys()
    assert data['total_builds'] == 7
