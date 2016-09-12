#!/usr/bin/env python3

from aiohttp import web
import traceback
import logging

from pony.orm import Database, Set, Required, db_session, Json, composite_key
from validate_email import validate_email

log = logging.getLogger("server")

# sql_debug(True)
db = Database()
db.bind('sqlite', ':memory:')
max_name_len = 255


def validate_emails(emails):
    if not isinstance(emails, list):
        return False
    if len(emails) < 1:   # as specified in the task
        return False
    if len(emails) > 10:  # suspiciously too many emails
        return False
    return all(validate_email(e) for e in emails)


class Person(db.Entity):
    fname = Required(str, max_name_len)
    lname = Required(str, max_name_len)
    composite_key(fname, lname)  # unique constraint on first and last names
    emails = Required(Json, py_check=validate_emails)
    groups = Set("Group")
    address_books = Set("AddressBook")


class Group(db.Entity):
    name = Required(str, max_name_len, unique=True)
    members = Set(Person)
    address_books = Set("AddressBook")


class AddressBook(db.Entity):
    name = Required(str, max_name_len, unique=True)
    people = Set(Person)
    groups = Set(Group)


def args_from_uri(f):
    async def match(self, request):
        args = request.match_info
        return await f(self, request, **args)
    return match


class OhMyRestRouter:

    def __init__(self, app, model, name=None):
        self.app = app
        self.model = model
        if name is None:
            name = model.__name__.lower()
        prefix = "/{name}".format(name=name)
        uri_name = lambda method: "{name}_{method}".format(
            name=name, method=method)
        app.router.add_route(
            'GET', prefix + r"/{id:\d+}", self.get, name=uri_name('get'))
        app.router.add_route(
            'PUT',
            prefix +
            r"/{id:\d+}/addto/{field:[a-z]+}",
            self.add,
            name=uri_name('add'))
        app.router.add_route('PUT', prefix, self.put, name=uri_name('put'))
        app.router.add_route('DELETE', prefix +
                             r"/{id:\d+}", self.delete, name=uri_name('del'))

    @args_from_uri
    async def get(self, request, id):
        id = int(id)
        with db_session:
            instance = self.model[id]
        instance_data = instance.to_dict()
        return web.json_response(instance_data)

    async def put(self, request):
        # await request.post()
        json_data = await request.json()
        print("JSON", json_data)
        log.debug("adding to the database: %s", json_data)
        with db_session:
            instance = self.model(**json_data)
            instance.flush()  # commit instance to populate id
            # import pdb; pdb.set_trace()
        instance_data = instance.to_dict()
        return web.json_response(instance_data)

    @args_from_uri
    async def add(self, request, id, field):
        id = int(id)
        field = getattr(self.model, field)
        assert isinstance(field, Set), "we can add only to Set() field"
        model = field.py_type  # model of item we are going to add

        json_data = await request.json()

        with db_session:
            instance = self.model[id]
            item = model[json_data['id']]
            collection = getattr(instance, field.name)  # get related field
            collection.add(item)
        result = item.to_dict()
        return web.json_response(result)

    @args_from_uri
    async def delete(self, request, id):
        id = int(id)
        with db_session:
            self.model[id].delete()


async def error_middleware(app, handler):
    """ Formats backend errors into json message. """
    def json_error(message):
        return web.json_response({'error': message}, status=500)

    async def middleware_handler(request):
        try:
            response = await handler(request)
            return response
        except Exception as ex:
            log.error("error while serving request:")
            traceback.print_last()
            return json_error(str(ex))
    return middleware_handler


def setup_app(loop=None):
    app = web.Application(middlewares=[error_middleware], loop=loop)
    OhMyRestRouter(app=app, model=Person)
    OhMyRestRouter(app=app, model=Group)
    OhMyRestRouter(app=app, model=AddressBook)
    db.generate_mapping(create_tables=True)
    return app


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description="Welcome to the most advanced calendar backend in the World!")
    parser.add_argument('--routes', default=False,
                        action='store_true', help="show routes")
    parser.add_argument('--shell', default=False,
                        action='store_true', help="launch IPython shell")
    parser.add_argument('--no-setup', default=False,
                        action='store_true', help="do not setup routes")
    parser.add_argument('-d', '--debug', default=False,
                        action='store_true', help="debug logging")
    args = parser.parse_args()

    if not args.no_setup:
        app = setup_app()

    if args.routes:
        if args.no_setup:
            print("please remove --no-setup to see routes")
        else:
            print("===== routes ======")
            for resource in app.router.resources():
                print("  ", resource)
            print("== end of routes ==")

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    if args.shell:
        from IPython import embed
        print("nothing really to do, spawning an interactive shell")
        with db_session:
            embed()
