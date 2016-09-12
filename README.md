## TL;DR

~~~
cd /tmp
git clone git@github.com:kopchik/interview_gingerpayments.git
cd interview_gingerpayments
virtualenv venv
source ./venv/bin/activate
pip install -r requirements.txt
pytest -s ./server_test.py
~~~

## Design
My first intention was to use Django REST, but I decided to try something new this time. So I chose aiohttp and ponyorm.

### PonyORM
Concerning Person and Group models.
One could use model inheritance so both people and groups could be easily add to a calendar.
But for the sake of simplicity address books have separate field for people and for groups.
I think this still conforms the specification.

I use **autopep8** (which is responsible for some weird formatting in the code),
**pyflakes** and **pylint** to ensure the best result.

Pros and cons of tools used:

I used JSON field for *Person.emails* because I always wanted to try it in conjunction with an SQL database
and to avoid extra tables ("denormalization"). Looks like it works, though requires manual  validation.

Pros:
1. Natively supports websockets (the main reason for me to use aiohttp)
1. Speed (arguable)
1. Transparency (no sophisticated machinery under the hood)


Cons:

1. No support for CORS/Auth in aiohttp
1. Schema migration is not yet there for ponyorm.
