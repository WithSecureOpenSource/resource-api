HTTP client
===========

HTTP clinet interface is similar in its design to :ref:`object interface <object_interface>`.

.. autoclass:: resource_api_http_client.client.Client
    :members: create, schema, get_resource_by_name

Root resource collection
------------------------

.. autoclass:: resource_api_http_client.client.RootResourceCollection
    :members: get, create

Resource collection
-------------------

.. autoclass:: resource_api_http_client.client.ResourceCollection
    :members: filter, count

Resource item
-------------

.. autoclass:: resource_api_http_client.client.ResourceInstance
    :members: update, delete, data, pk, links

Link holder
-----------

.. autoclass:: resource_api_http_client.client.LinkHolder

Root link collection
--------------------

.. autoclass:: resource_api_http_client.client.RootLinkCollection
    :members: get, create

Link collection
---------------

.. autoclass:: resource_api_http_client.client.LinkCollection
    :members: filter, count

Link instance
-------------

.. autoclass:: resource_api_http_client.client.LinkInstance
    :members: update, delete, data, target

Link to one
-----------

.. autoclass:: resource_api_http_client.client.LinkToOne
    :members: set, item
