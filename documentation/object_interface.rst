.. _object_interface:

Object interface
================

Object interface is accessible via so called *entry point*. Check :ref:`here <entry_point>` to understand how entry
points are obtained.

*NOTE*: Whenever user performs an operation and the operation fails one of :ref:`built-in exceptions <errors>` is
raised.

.. autoclass:: resource_api.service.EntryPoint
    :members:

Root resource collection
------------------------

.. autoclass:: resource_api.resource.RootResourceCollection
    :members: get, create

Resource collection
-------------------

.. autoclass:: resource_api.resource.ResourceCollection
    :members: filter, count

Resource item
-------------

.. autoclass:: resource_api.resource.ResourceInstance
    :members: update, delete, data, pk, links

Link holder
-----------

.. autoclass:: resource_api.link.LinkHolder

Root link collection
--------------------

.. autoclass:: resource_api.link.RootLinkCollection
    :members: get, create

Link collection
---------------

.. autoclass:: resource_api.link.LinkCollection
    :members: filter, count

Link instance
-------------

.. autoclass:: resource_api.link.LinkInstance
    :members: update, delete, data, target

Link to one
-----------

.. autoclass:: resource_api.link.LinkToOne
    :members: set, item
