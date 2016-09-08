## TL;DR

~~~
virtualenv venv
source ./venv/bin/activate
~~~

## Design
My first intention was to use Django REST, but I decided to try something new this time.

One could use model inheritance so both people and groups could be easily add to calendar.
But for the sake of simplicity addres books have separate field for people and for groups.
I think this still conforms the specification.

I use autopep8 (which is responsible for some weird formatting in the code),
pyflakes and pylint to ensure the best result.

Pros and cons of tools used:

I used JSON because I always wanted to try it in conjuction with an SQL database
and to avoid extra tables ("denormalization").

Pros:  
1. Natively supports websockets (main reason I user aiohttp)
1. Speed (arguable)
1. Transparency


Cons:

1. No support for CORS/Auth in aiohttp
1. Schema migration is not yet there for ponyorm.
