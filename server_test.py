from server import setup_app
import pytest
pytest_plugins = 'aiohttp.pytest_plugin'

from faker import Faker
from random import randint
import logging
import json

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


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
    log.debug("URI resolved to %s", uri)
    json_data = json.dumps(data)
    resp = await client.request(method, uri, data=json_data)
    assert resp.status == 200
    json_resp = await resp.json()
    return json_resp


def gen_fake_user():
    faker = Faker()
    name = faker.name()
    fname, lname = name.split(maxsplit=1)
    emails = [faker.email() for _ in range(randint(2, 3))]
    data = {'fname': fname, 'lname': lname, 'emails': emails}
    log.debug("new fake user: %s", data)
    return data


async def test_creation(client):
    # create new object
    person = await jsonreq(client, 'person_put', gen_fake_user())

    # can we retrieve what we just created?
    person2 = await jsonreq(client, 'person_get', id=person['id'])
    assert person2 == person, "created and retrevied objects do not match"

    person3 = await jsonreq(client, 'person_put', gen_fake_user())

    calendar = await jsonreq(client, 'addressbook_put', {"name": "a calendar"})

    calendar = await jsonreq(client, 'addressbook_add', person3, id=calendar['id'], field="people")
    print("!", calendar)
