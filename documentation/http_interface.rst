.. _http_interface:

HTTP interface
==============

Resource API can be exposed via HTTP interface with 2nd level of
`REST Maturity Model <http://martinfowler.com/articles/richardsonMaturityModel.html>`_

It can be achieved by passing Resource API service instance to
:class:`WSGI application <resource_api_http.http.Application>`:

.. code-block:: python

    from werkzeug.serving import run_simple
    from custom_app.service import CustomService
    from resource_api_http.http import Application

    srv = CustomService()
    app = Application(srv, debug=True)
    run_simple('127.0.0.1', 5000, app, use_debugger=True, use_reloader=True)

*NOTE*: there is no need to call :meth:`setup() <resource_api.service.Service.setup>` method before passing the service
to WSGI app. WSGI app shall make the call itself.

General principles
------------------

  - structure of the resource is not exposed via URL schema
  - links between the resources are exposed via URL schema
  - it is not be possible to get links related to the resource via the same url as the resource itself
  - there isn't any url to get a collection of the resources' representations. Instead there are URLs to get a list of
    URIs first and later on use individual HTTP requests to fetch representations of each resource.
  - all resources have one and only one URI

URL schema
----------

Http service has the follwoing URL schema:

::

    LINK = RELATIONSHIP
    RESOURCE_NAME = NAMESPACE.ACTUAL_RESOURCE_NAME
    ID = Individual resource's URI
    LINK_NAME = Name of the relationship in a triple
    TARGET_ID = URI of the target resource in relationship's triple

    # has to contain all required fields
    {new_link_data} = {"@target": TARGET_PK, key: value}
    # has to contain only the fields to be changed. Can't contain "@target".
    {partial_link_data} = {key: value}

    # has to contain all required fields
    {new_resource_data} = {key: value, "@links": {link_to_many_name: [{new_link_data}, ...],
                                                  link_to_one_name: {new_link_name}}}
    # has to contain only the fields to be changed. Can't contain "@links".
    {partial_resource_data} = {key: value}  # does not have to contain all fields


    ## Schema

    OPTIONS /
    >> {service_schema}

    ## Resource operations

      # create new resource
      POST {new_resource_data} /RESOURCE_NAME
      >> PK, 201 || None, 204

      # get a collection of IDs
      GET /RESOURCE_NAME
      >> [ID1, ID2, ..., IDN], 200

      # get a filtered collection of IDs
      GET /RESOURCE_NAME?query_param=value
      >> [ID1, ID2, ..., IDN], 200

      # get resource's representation
      GET /RESOURCE_NAME/ID
      >> {key: value}, 200

      # update certain fields of the resource
      PATCH {partial_resource_data} /RESOURCE_NAME/ID
      >> None, 204

      # remove the resource
      DELETE /RESOURCE_NAME/ID
      >> None, 204

      # get number of resources
      GET /RESOURCE_NAME:count
      >> integer count, 200

      # get number of resources with filtering
      GET /RESOURCE_NAME:count?query_param=value
      >> integer count, 200

    ## Link operations

      ### Link to one operations

        NOTE: "link" string is a part of the URL

        # get target resource's ID
        GET /RESOURCE_NAME/ID/LINK_NAME/item
        >> TARGET_ID, 200

        # update the link
        PATCH /RESOURCE_NAME/ID/LINK_NAME/item {partial_link_data}
        >> None, 204

        # create a new link or completely overwrite the existing one
        PUT /RESOURCE_NAME/ID/LINK_NAME {new_link_data}
        >> None, 204

        # get data related to the link
        GET /RESOURCE_NAME/ID/LINK_NAME/item:data
        >> {key: value}, 200

        # remove the link
        DELETE /RESOURCE_NAME/ID/LINK_NAME/item
        >> None, 204

      ### Link to many operations

        # get a collection of TARGET_IDs
        GET /RESOURCE_NAME/ID/LINK_NAME
        >> [TARGET_ID1, TARGET_ID2, ...], 200

        # get a filtered collection of TARGET_IDs
        GET /RESOURCE_NAME/ID/LINK_NAME?query_param=value
        >> [TARGET_ID1, TARGET_ID2, ...], 200

        # get number of links
        GET /RESOURCE_NAME/ID/LINK_NAME:count
        >> integer count, 200

        # get number of links with filtering
        GET /RESOURCE_NAME/ID/LINK_NAME:count?query_param=value
        >> integer count, 200

        # create a new link
        POST /RESOURCE_NAME/ID/LINK_NAME {new_link_data}
        >> None, 204

        # get data related to the link
        GET /RESOURCE_NAME/ID/LINK_NAME/TARGET_ID:data
        >> {partial_link_data}, 200

        # update the link
        PATCH /RESOURCE_NAME/ID/LINK_NAME/TARGET_ID {partial_link_data}
        >> None, 204

        # remove the link
        DELETE /RESOURCE_NAME/ID/LINK_NAME/TARGET_ID
        >> None, 204


Error status codes
------------------

  - **400** in case if request body is invalid
  - **403** for any issue related to user authentication/authorization. E.g. if user has no permission to change
    certain fields.
  - **404** if the resource/link being accessed does not exist
  - **405** when some HTTP method is not allowed with a specific URL
  - **409** when trying to perform the operation that causes conflicts
  - **501** when some functionality is not implemented
  - **500** when unknown server error takes place

WSGI Application reference
--------------------------

.. autoclass:: resource_api_http.http.Application
