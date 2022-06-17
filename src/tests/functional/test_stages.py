from json import loads

def test_get_stages(test_client):
    'HU5 - Escenario 1 parte 4'
    'Dado que existe al menos un proyecto asociado al equipo de desarrollo y está registrada la fuente de información de Jira'
    'Cuando el líder de proyectos accede al dashboard del equipo de desarrollo'
    'Entonces se genera el dashboard a partir de los datos extraídos de las fuentes de información registradas'

    team_project_id = '629f70971785c7fd81349a19'
    source_id = '629f70971785c7fd81349a1a'

    client, mongo = test_client

    response = client.post('/jenkins/stages', json={
        'team_project_id': team_project_id, 
        'source_id': source_id
    })

    data_str = response.data.decode('utf8')

    data = loads(data_str)

    for stage in data.keys():
        assert 'stages_names' in data[stage].keys()
        assert 'count' in data[stage].keys()
        assert len(data[stage]['stages_names']) == data[stage]['count']