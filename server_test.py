from server import setup_app
import pytest
pytest_plugins = 'aiohttp.pytest_plugin'
from faker import Faker
from random import randint


@pytest.fixture
def client(loop, test_client):
    return loop.run_until_complete(test_client(setup_app))

async def jsonreq(client, route_name, data=None, **parts):
    """ A little helper to make reverse URL mappings less painful in aiohttp 0.21+ """

    app = client.app
    resource = app.router[route_name]
    method = resource._routes[0].method
    if 'formatter' in resource.get_info():
        uri = resource.url(parts=parts)
    else:
        uri = resource.url()
    resp = await client.request(method, uri, data=data)
    assert resp.status == 200
    json = await resp.json()
    return json


def gen_fake_user():
    faker = Faker()
    name = faker.name()
    fname, lname = name.split()
    emails = [faker.email() for _ in range(randint(1, 3))]
    data = {'fname': fname, 'lname': lname, 'emails': emails}
    print(data)
    return data

async def test_creation(client):
    # create new object
    json = await jsonreq(client, 'person_put', gen_fake_user())
    print(json)

    # retreive it
    json2 = await jsonreq(client, 'person_get', id=json['id'])
    assert json2 == json, "created and retrevied objects do not match"

    json = await jsonreq(client, 'person_put', gen_fake_user())
    print(json)
