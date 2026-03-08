import pytest


@pytest.mark.django_db
def test_view_page_requires_login(client):
    """FR-03: Unauthenticated user is redirected to /login/."""
    response = client.get('/')
    assert response.status_code == 302
    assert '/login/' in response['Location']


@pytest.mark.django_db
def test_edit_page_requires_login(client):
    """FR-03: Unauthenticated user is redirected to /login/ from /edit/."""
    response = client.get('/edit/')
    assert response.status_code == 302
    assert '/login/' in response['Location']


@pytest.mark.django_db
def test_login_page_accessible_without_auth(client):
    """FR-01: Login page is reachable without authentication."""
    response = client.get('/login/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_login_success_redirects_to_view(client, django_user_model):
    """FR-01: Correct credentials redirect to / (view page)."""
    django_user_model.objects.create_user(username='alice', password='pass1234')
    response = client.post('/login/', {'username': 'alice', 'password': 'pass1234'})
    assert response.status_code == 302
    assert response['Location'] == '/'


@pytest.mark.django_db
def test_login_failure_shows_error(client, django_user_model):
    """FR-01: Wrong credentials show error message."""
    response = client.post('/login/', {'username': 'nobody', 'password': 'wrong'})
    assert response.status_code == 200
    assert 'Неверный email или пароль' in response.content.decode()


@pytest.mark.django_db
def test_logout_redirects_to_login(auth_client):
    """FR-02: Logout ends session and redirects to /login/."""
    response = auth_client.get('/logout/')
    assert response.status_code == 302
    assert '/login/' in response['Location']


@pytest.mark.django_db
def test_authenticated_user_can_access_view_page(auth_client):
    """Authenticated user can reach the view page."""
    response = auth_client.get('/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_authenticated_user_can_access_edit_page(auth_client):
    """Authenticated user can reach the edit page."""
    response = auth_client.get('/edit/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_already_logged_in_redirected_from_login(auth_client):
    """Authenticated user opening /login/ is redirected to /."""
    response = auth_client.get('/login/')
    assert response.status_code == 302
    assert response['Location'] == '/'
