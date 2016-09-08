#!/usr/bin/env python3

from aiohttp import web
import asyncio


from pony.orm import *

# sql_debug(True)
db = Database()
db.bind('sqlite', ':memory:')


class Person(db.Entity):
    fname = Required(str, 255)
    lname = Required(str, 255)
    emails = Required(Json)
    groups = Set("Group")
    address_books = Set("AddressBook")


class Group(db.Entity):
    members = Set(Person)
    address_books = Set("AddressBook")


class AddressBook(db.Entity):
    name = Required(str, 255)
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
        await request.post()
        data = request.POST
        with db_session:
            instance = self.model(**data)
            instance.flush()
            # import pdb; pdb.set_trace()
        instance_data = instance.to_dict()
        return web.json_response(instance_data)

    @args_from_uri
    async def delete(self, request, id):
        id = int(id)
        with db_session:
            self.model[id].delete()




def json_error(message):
    return web.json_response({'error': message})

async def error_middleware(app, handler):
    async def middleware_handler(request):
        try:
            response = await handler(request)
            return response
        except Exception as ex:
            print("ERROR:", ex)
            return json_error(ex)
    return middleware_handler

app = web.Application(middlewares=[error_middleware])


def setup_app(loop=None):
    app = web.Application(loop=loop)
    OhMyRestRouter(app=app, model=Person)
    db.generate_mapping(create_tables=True)
    return app





# from IPython import embed
# with db_session:
#     embed()


