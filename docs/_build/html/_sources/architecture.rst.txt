Architecture
============

PhotoShare uses a layered application architecture.

Application Flow
----------------

::

    HTTP request
         |
         v
      routes
         |
         v
      services
         |
         v
    repositories
         |
         v
    SQLAlchemy ORM
         |
         v
     PostgreSQL


Routes
------

Modules in ``src.routes`` define the FastAPI HTTP endpoints.

They are responsible for:

* receiving HTTP requests;
* resolving FastAPI dependencies;
* checking access permissions;
* returning HTTP responses;
* defining HTTP status codes.


Services
--------

Modules in ``src.services`` contain the application business logic.

The main services include:

* JWT handling and password hashing;
* authentication;
* authorization and permissions;
* Cloudinary integration;
* image transformations;
* QR code generation;
* tag normalization.


Repositories
------------

Modules in ``src.repository`` isolate SQLAlchemy database operations
from the HTTP layer of the application.

They are responsible for:

* SELECT operations;
* INSERT operations;
* UPDATE operations;
* DELETE operations;
* aggregation;
* searching and filtering.


Entities
--------

Modules in ``src.entity`` contain SQLAlchemy ORM models.

The main entities are:

* User;
* Photo;
* Tag;
* Comment;
* Rating;
* PhotoTransform;
* TokenBlacklist.


Schemas
-------

Modules in ``src.schemas`` contain Pydantic models used for:

* request data validation;
* response models;
* value constraints;
* data normalization.


Authentication and Authorization
--------------------------------

PhotoShare uses JWT Bearer authentication.

The application supports the following roles:

* ``user``;
* ``moderator``;
* ``admin``.

The first registered user automatically receives the ``admin`` role.

Administrators can manage user roles and account status.
Moderators and administrators have additional permissions for
managing comments and ratings.


Storage
-------

PostgreSQL stores the application metadata.

Cloudinary stores:

* uploaded photos;
* generated QR code images.

Transformed image versions are represented by Cloudinary
transformation URLs.


Database Migrations
-------------------

Alembic is used to manage the PostgreSQL database schema.

Before the application container starts, the following command is run:

::

    alembic upgrade head


Docker
------

The application can be run using Docker and Docker Compose.

The API container starts Uvicorn after all pending Alembic migrations
have been successfully applied.


Testing
-------

The project uses pytest for automated testing.

The test suite covers:

* authentication;
* user roles and permissions;
* photo operations;
* comments;
* ratings;
* searching and filtering;
* image transformations;
* Cloudinary integration;
* QR code generation;
* JWT blacklist behavior.