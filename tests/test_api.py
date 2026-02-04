"""Basic API tests."""
import json


def test_api_docs_accessible(client):
    """Test that Swagger docs are accessible."""
    response = client.get('/api/docs')
    assert response.status_code == 200


def test_create_domain(client):
    """Test creating a domain."""
    response = client.post('/api/domains',
                           data=json.dumps({'name': 'test.com', 'description': 'Test domain'}),
                           content_type='application/json')
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['name'] == 'test.com'


def test_list_domains(client):
    """Test listing domains."""
    # Create a domain first
    client.post('/api/domains',
                data=json.dumps({'name': 'test.com'}),
                content_type='application/json')

    response = client.get('/api/domains')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1


def test_create_config(client):
    """Test creating a config for a domain."""
    # Create domain first
    resp = client.post('/api/domains',
                       data=json.dumps({'name': 'test.com'}),
                       content_type='application/json')
    domain_id = json.loads(resp.data)['id']

    # Create config
    response = client.post(f'/api/domains/{domain_id}/configs',
                           data=json.dumps({
                               'language': 'zh-CN',
                               'data': {'title': '测试标题'}
                           }),
                           content_type='application/json')
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['language'] == 'zh-CN'
    assert data['data']['title'] == '测试标题'


def test_query_config(client):
    """Test querying config with language fallback."""
    # Create domain and config
    resp = client.post('/api/domains',
                       data=json.dumps({'name': 'test.com'}),
                       content_type='application/json')
    domain_id = json.loads(resp.data)['id']

    client.post(f'/api/domains/{domain_id}/configs',
                data=json.dumps({
                    'language': 'zh-CN',
                    'data': {'title': '中文标题'}
                }),
                content_type='application/json')

    # Query with zh-CN
    response = client.get('/api/query?domain=test.com&lang=zh-CN')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['language'] == 'zh-CN'
    assert data['is_fallback'] is False

    # Query with en (should fallback to zh-CN)
    response = client.get('/api/query?domain=test.com&lang=en')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['language'] == 'zh-CN'
    assert data['is_fallback'] is True


def test_domain_not_found(client):
    """Test 404 for non-existent domain."""
    response = client.get('/api/domains/999')
    assert response.status_code == 404


def test_duplicate_domain(client):
    """Test 409 for duplicate domain."""
    client.post('/api/domains',
                data=json.dumps({'name': 'test.com'}),
                content_type='application/json')

    response = client.post('/api/domains',
                           data=json.dumps({'name': 'test.com'}),
                           content_type='application/json')
    assert response.status_code == 409
