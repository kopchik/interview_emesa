from server import setup_app
import pytest
pytest_plugins = 'aiohttp.pytest_plugin'

from faker import Faker
from random import randint
import logging
import json

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)
faker = Faker()  # fake user data generator


@pytest.fixture
def client(loop, test_client):
    return loop.run_until_complete(test_client(setup_app))


async def jsonreq(client, route_name, data=None, query=None, **parts):
    """ A little helper to make reverse URL mappings less painful in aiohttp 0.21+ """

    app = client.app
    resource = app.router[route_name]
    method = resource._routes[0].method
    if 'formatter' in resource.get_info():
        uri = resource.url(parts=parts, query=query)
    else:
        uri = resource.url(query=query)
    log.debug("URI resolved to %s", uri)
    json_data = json.dumps(data)
    resp = await client.request(method, uri, data=json_data)
    assert resp.status == 200
    json_resp = await resp.json()
    return json_resp


def gen_fake_user():
    name = faker.name()
    fname, lname = name.split(maxsplit=1)
    emails = [faker.email() for _ in range(randint(2, 3))]
    data = {'fname': fname, 'lname': lname, 'emails': emails}
    log.debug("new fake user: %s", data)
    return data


async def test_basic_operations(client):
    # create new person
    person1 = await jsonreq(client, 'person_put', gen_fake_user())

    # can we retrieve what we just created?
    person2 = await jsonreq(client, 'person_get', id=person1['id'])
    assert person2 == person1, "created and retrevied objects do not match"

    # okay, add some new person
    person3 = await jsonreq(client, 'person_put', gen_fake_user())

    # create a few group
    group1 = await jsonreq(client, 'group_put', {"name": "some group"})
    group2 = await jsonreq(client, 'group_put', {"name": "nother group"})

    # create address_book
    address_book = await jsonreq(client, 'addressbook_put', {"name": "some address_book"})

    # add a person to the address_book
    address_book = await jsonreq(client, 'addressbook_add', person1, id=address_book['id'], field="people")
    assert person1['id'] in address_book['people']
    assert person3['id'] not in address_book['people']

    # get a person with a list of groups
    person1 = await jsonreq(client, 'person_get', gen_fake_user(), id=person1['id'])
    assert address_book['id'] in person1['address_books']

    # add a group to the address_book
    address_book = await jsonreq(client, 'addressbook_add', group1, id=address_book['id'], field="groups")
    assert group1['id'] in address_book['groups']
    assert group2['id'] not in address_book['groups']


async def test_search_by_name(client):
    # check that we can search by first name
    person = await jsonreq(client, 'person_put', dict(fname="_fname", lname="_lname", emails=["test@example.com"]))
    people = await jsonreq(client, 'person-find', query=dict(fname="_fname"))
    assert len(people) == 1 and person in people

    # check search by last name
    people = await jsonreq(client, 'person-find', query=dict(lname="_lname"))
    assert len(people) == 1 and person in people

    # check search by first and last names
    people = await jsonreq(client, 'person-find', query=dict(fname="_fname", lname="_lname"))
    assert len(people) == 1 and person in people


async def test_search_by_email(client):
    person = await jsonreq(client, 'person_put', dict(fname="somename", lname="somesurname", emails=["another@example.com"]))
    people = await jsonreq(client, 'person-find-by-email', query=dict(email="another@example.com"))
    assert len(people) == 1 and person in people
