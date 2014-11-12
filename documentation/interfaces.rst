.. _interfaces:

Interfaces
==========

There are two major entities in this framework: resources and links between them.

Resource API defines interfaces to be implemented in order to expose the entities.

**NOTE**: all methods must be implemnted. In case if some of the methods are not supposed to do anything, raise
*NotImplemntedError* within their implementations and return *False* for respective authorization methods if needed.

Resource
--------

Resource concept is similar to
`the one mentioned <http://www.ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm#sec_5_2_1_1>`_
in Roy Fielding's desertation.

.. autoclass:: resource_api.interfaces.Resource
    :members:
    :special-members: __init__

URI is represented by a PK (Primary Key) in Resource API.

Resource interface defines two types of methods.

First, `DAL <http://en.wikipedia.org/wiki/Data_access_layer>`_ related
`CRUD <http://en.wikipedia.org/wiki/Create,_read,_update_and_delete>`_ methods: get_data, get_pks, set, delete, exists

Second, authorization related methods starting with *can_*

Each resource must define a **UriPolicy**:

.. autoclass:: resource_api.interfaces.AbstractUriPolicy
    :members:
    :special-members: __init__

The default pk policy is this one:

.. autoclass:: resource_api.interfaces.PkUriPolicy

Note, there are certain cases when the URI is supposed to be generated within peristence (data acess) layer. E.g.
via autoincrementing primary key in SQL database. In such case the URI is supposed to be returned by *create* method.

.. code-block:: python

    class Example(Resource):

        class UriPolicy(AbstractUriPolicy):

            def deserialize(self, pk):
                try:
                    return int(pk)
                except ValueError:
                    raise ValidationError("URI is not int")

            def serialize(self, pk):
                return pk

            @property
            def type(self):
                return "autoincrement_pk_policy"

            def generate_pk(self, data, link_data=None):
                return None

        def create(self, pk, data):
            # assert pk is None
            row_id = self._sql_database.create_row(data)
            return row_id

        ...

Link
----

Link concept is derived from `RDF triples <http://www.robertprice.co.uk/robblog/2004/10/what_is_an_rdf_triple_-shtml/>`_
. `RDF <http://www.w3.org/RDF/>`_ is at the same time a part of two big W3C standardized concepts:
`Linked Data <http://linkeddata.org/>`_ and
`Semantic Web <http://semanticweb.org/>`_.

NOTE: Resource API does not aim to follow any of standards defined by the
concepts mentioned above. It just uses a portion of interesting ideas that those concepts describe.

.. autoclass:: resource_api.interfaces.Link
    :members:
    :special-members: __init__

Link interface defines two types of methods similar to the ones of Resource interface.

There are conceptual differences between those methods in Link and Resource though.

First, link uses a triple (mentioned above) to address exisiting entities.

Second, data is optional for links.

It is critical to note that *predicate* part of a triple is not passed to any of Link methods. Since all links are
supposed to be defined via nested classes in the context of resources they connect - link classes themselves serve as
those *predicates*.

Link declaration
----------------

Links between resources are defined using nested classes:

.. code-block:: python

    class Course(Resource):

        class Links:

            class attendants(Link):
                target = "Student"
                related_name = "active_cources"
                master = True

                def get(self, pk, rel_pk):
                    ...

    class Student(Resource):

        class Links:

            class active_cources(Link):
                target = "Course"
                related_name = "attendants"

                def get(self, pk, rel_pk):
                    ...

*target* has to be a string. It can point to a resource in the same module ("Target") or in any other one
("module.name.Target"). *related_name* must be defined as a string as well and it should equal to the name of a related
link.

Also one of the links must be defined as a *master* one. Authorization is done against *master* link. And extra data
is stored only in DAL related to *master* link.

Any link can be marked as *changeable = False*. Unchangeable links can be set only upon resource creation. Once the
resource is created links cannot be modified (i.e. updated/set or deleted).

All link declarations must be done within *Links* inner class.

One way links
-------------

.. note::

    If the link is marked as *one_way* Resource API will not be able to enforce relational integrity.

One way links do not need a *related_name* nor a *master* flag to be defined. One way links can be declared the
following way:

.. code-block:: python

    class Source(Resource):

        class Links:

            class targets:
                target = "foo.bar.Target"
                one_way = True


Link cardinality
----------------

More on relationship cardinality - `here <http://en.wikipedia.org/wiki/Cardinality_(data_modeling)>`_.

MANY to ONE relationship can be defined this way:

.. code-block:: python

    class Target(Resource):

        class Links:

            class sources(Link):
                cardinality = Link.cardinalities.MANY # could be ommited - it is the default one
                target = "Source"
                related_name = "target"

    class Source(Resource):

        class Links:

            class target(Link):
                cardinality = Link.cardinalities.ONE
                target = "Target"
                related_name = "sources"
                master = True
    ...

ONE to ONE relationship can be defined this way:

.. code-block:: python

    class Target(Resource):

        class Links:

            class source(Link):
                cardinality = Link.cardinalities.ONE
                target = "Source"
                related_name = "target"

    class Source(Resource):

        class Links:

            class target(Link):
                cardinality = Link.cardinalities.ONE
                target = "Target"
                related_name = "source"
                master = True
    ...

MANY to MANY is the default one but explicitly can be defined this way:

.. code-block:: python

    class Target(Resource):

        class Links:

            class sources(Link):
                cardinality = Link.cardinalities.MANY # could be ommited - it is the default one
                target = "Source"
                related_name = "targets"

    class Source(Resource):

        class Links:

            class targets(Link):
                cardinality = Link.cardinalities.MANY # could be ommited - it is the default one
                target = "Target"
                related_name = "sources"
                master = True
    ...

*NOTE*: relationships with cardinality ONE can be marked as required:

.. code-block:: python

    class Target(Resource):

        class Links:

            class sources(Link):
                cardinality = Link.cardinalities.MANY # could be ommited - it is the default one
                target = "Source"
                related_name = "target"

    class Source(Resource):

        class Links:

            class target(Link):
                cardinality = Link.cardinalities.ONE
                target = "Target"
                related_name = "sources"
                required = True
                master = True
    ...

Relationships with *MANY* cardinality cannot be marked as *required*.

In case of required relationships, data for them must be passed together with main resource data during creation phase.

Schema and QuerySchema
----------------------

Resources and Links may define schema that shall be used via Resource API for input validation.

The schema is defined the following way:

.. code-block:: python

    class CustomResource(Resource):

        class Schema:
            name = schema.StringField(pk=True)
            count = schema.IntegerField()

        class Links:

            class target(Link):
                class Schema:
                    timestamp = schema.DateTimeField()

Schema fields are defined within a nested class with a reserved name *Schema*. A comprehensive reference for built-in
fields can be found :ref:`here <schema>`.

Additionally both Resources and Links may define query schema to validate all parameters that client uses for
filtering the collections.

Query schema is defined the following way:

.. code-block:: python

    class CustomResource(Resource):

        class QuerySchema:
            name = schema.StringField(pk=True)
            count = schema.IntegerField()

        class Links:

            class target(Link):
                class QuerySchema:
                    timestamp = schema.DateTimeField()

Query parameters are defined in a similar manner as *Schema* ones but inside *QuerySchema* nested subclass. The key
functional difference between two schemas is the fact that *Schema* may have **required** fields and *QuerySchema* may
not.

*NOTE*: it is not necessary for *Schema* and *QuerySchema* inner classes to inherit from *Schema* class. Resource API
adds this inheritance automatically.
