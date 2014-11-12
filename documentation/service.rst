Service and registry
====================

Service class
-------------

The entity main in Resource API is called *Service*.

.. autoclass:: resource_api.service.Service
    :members:
    :private-members: _get_context, _get_user

Resource registration
---------------------

Lets say that there are multiple resources declared somewhere. In this case they can be registered the following way:

.. code-block:: python

    class MultiSQLService(Service):

        def _get_context(self):
            return {
                "db1": create_connection(...),
                "db2": create_connection(...)
            }

    srv = MultiSQLService()
    srv.register(Student)
    srv.register(Teacher)
    srv.register(Course)
    srv.setup()

.. _entry_point:

Entry point
-----------

In order to get access to the :ref:`object interface <object_interface>` user must call *get_entry_point* method.

.. code-block:: python

    entry_point = srv.get_entry_point({"username": "FOO"})
