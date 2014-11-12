"""
Copyright (c) 2014-2015 F-Secure
See LICENSE for details
"""
import json
import logging
import traceback
from functools import partial

from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug import exceptions as http_exceptions

from resource_api.schema import ListField, ObjectField
from resource_api import errors


def _preprocess_query(schema, args):
    rval = {}
    for key in args.keys():
        field = getattr(schema, key, None)
        if field is None:
            continue
        elif isinstance(field, ListField):
            rval[key] = args.getlist(key)
        elif isinstance(field, ObjectField):
            try:
                rval[key] = json.loads(args.get(key))
            except ValueError, e:
                errors.ValidationError({key: e})
        else:
            rval[key] = args.get(key)
    return rval


def get_schema(request, service):
    return service.get_schema(), 200


def _get_col(request, service, resource_name):
    res = service.get_entry_point(request.headers).get_resource_by_name(resource_name)
    args = _preprocess_query(res._res.query_schema, request.args)
    if args:
        return res.filter(params=args)
    else:
        return res


def get_resource_collection(request, service, resource_name):
    return _get_col(request, service, resource_name).serialize(), 200


def get_resource_collection_count(request, service, resource_name):
    return _get_col(request, service, resource_name).count(), 200


def get_resource_item(request, service, resource_name, resource_pk):
    res = service.get_entry_point(request.headers).get_resource_by_name(resource_name).get(resource_pk)
    if request.method == "HEAD":
        return None, 200
    else:
        return res.serialize(), 200


def delete_resource_item(request, service, resource_name, resource_pk):
    return service.get_entry_point(request.headers).get_resource_by_name(resource_name)\
                  .get(resource_pk).delete(), 204


def update_resource_item(request, service, resource_name, resource_pk):
    return service.get_entry_point(request.headers).get_resource_by_name(resource_name)\
                  .get(resource_pk).update(json.loads(request.data)), 204


def create_resource_item(request, service, resource_name):
    resource_data = json.loads(request.data)
    links = resource_data.pop("@links", {})
    return service.get_entry_point(request.headers).get_resource_by_name(resource_name)\
                  .create(resource_data, links).serialize_pk(), 201


def _get_link_col(request, service, resource_name, resource_pk, link_name):
    links = service.get_entry_point(request.headers).get_resource_by_name(resource_name).get(resource_pk).links
    lnk = getattr(links, link_name)
    args = _preprocess_query(lnk._forward_link_instance.query_schema, request.args)
    if args:
        return lnk.filter(params=args)
    else:
        return lnk


def get_link_to_many_collection(request, service, resource_name, resource_pk, link_name):
    return _get_link_col(request, service, resource_name, resource_pk, link_name).serialize(), 200


def get_link_to_many_collection_count(request, service, resource_name, resource_pk, link_name):
    return _get_link_col(request, service, resource_name, resource_pk, link_name).count(), 200


def update_link_to_many_item(request, service, resource_name, resource_pk, link_name, target_pk):
    links = service.get_entry_point(request.headers).get_resource_by_name(resource_name).get(resource_pk).links
    return getattr(links, link_name).get(target_pk).update(json.loads(request.data)), 204


def delete_link_to_many_item(request, service, resource_name, resource_pk, link_name, target_pk):
    links = service.get_entry_point(request.headers).get_resource_by_name(resource_name).get(resource_pk).links
    return getattr(links, link_name).get(target_pk).delete(), 204


def get_link_to_many_item_data(request, service, resource_name, resource_pk, link_name, target_pk):
    links = service.get_entry_point(request.headers).get_resource_by_name(resource_name).get(resource_pk).links
    link = getattr(links, link_name).get(target_pk)
    if request.method == "HEAD":
        return None, 200
    else:
        return link.serialize(), 200


def create_link_to_many_item(request, service, resource_name, resource_pk, link_name):
    links = service.get_entry_point(request.headers).get_resource_by_name(resource_name).get(resource_pk).links
    link_item = getattr(links, link_name).create(json.loads(request.data))
    return link_item.target.serialize_pk(), 201


def set_link_to_one(request, service, resource_name, resource_pk, link_name):
    links = service.get_entry_point(request.headers).get_resource_by_name(resource_name).get(resource_pk).links
    link = getattr(links, link_name)
    link.set(json.loads(request.data))
    return link.item.target.serialize_pk(), 201


def delete_link_to_one(request, service, resource_name, resource_pk, link_name):
    links = service.get_entry_point(request.headers).get_resource_by_name(resource_name).get(resource_pk).links
    getattr(links, link_name).item.delete()
    return None, 204


def update_link_to_one(request, service, resource_name, resource_pk, link_name):
    links = service.get_entry_point(request.headers).get_resource_by_name(resource_name).get(resource_pk).links
    getattr(links, link_name).item.update(json.loads(request.data))
    return None, 204


def get_link_to_one_data(request, service, resource_name, resource_pk, link_name):
    links = service.get_entry_point(request.headers).get_resource_by_name(resource_name).get(resource_pk).links
    link = getattr(links, link_name).item
    if request.method == "HEAD":
        return None, 200
    else:
        return link.serialize(), 200


def get_link_to_one_target(request, service, resource_name, resource_pk, link_name, redirect=False):
    links = service.get_entry_point(request.headers).get_resource_by_name(resource_name).get(resource_pk).links
    link = getattr(links, link_name)
    return link.item.target.serialize_pk(), 200


class Application(object):
    """ Plain WSGI application for Resource API service

    service (:class:`Service's <resource_api.service.Service>` subclass instance)
        Service to generate HTTP interface for
    debug (bool)
        If True 500 responses will include detailed traceback describing the error
    """

    def __init__(self, service, debug=False):
        service.setup()
        url_map = []

        def rule(url, endpoint, method="GET", **kwargs):
            url_map.append(Rule(url, methods=[method], endpoint=partial(endpoint, **kwargs)))

        rule("/", get_schema, service=service, method="OPTIONS")

        schema = service.get_schema()

        for resource_name, resource_meta in schema.iteritems():
            kwargs = dict(resource_name=resource_name, service=service)

            rule("/%s" % resource_name, get_resource_collection, **kwargs)
            rule("/%s:count" % resource_name, get_resource_collection_count, **kwargs)
            rule("/%s" % resource_name, create_resource_item, "POST", **kwargs)
            rule("/%s/<resource_pk>" % resource_name, get_resource_item, "GET", **kwargs)
            rule("/%s/<resource_pk>" % resource_name, delete_resource_item, "DELETE", **kwargs)
            rule("/%s/<resource_pk>" % resource_name, update_resource_item, "PATCH", **kwargs)

            for link_name, link_meta in resource_meta.get("links", {}).iteritems():
                kwargs = dict(kwargs)
                kwargs["link_name"] = link_name
                base_url = "/%s/<resource_pk>/%s" % (resource_name, link_name)

                def link_rule(endpoint, suffix="", method="GET"):
                    rule(base_url + suffix, endpoint, method, **kwargs)

                if link_meta.get("cardinality", "MANY") == "ONE":
                    link_rule(get_link_to_one_target, suffix="/item")
                    link_rule(set_link_to_one, method="PUT")
                    link_rule(get_link_to_one_data, suffix="/item:data")
                    link_rule(update_link_to_one, method="PATCH", suffix="/item")
                    link_rule(delete_link_to_one, method="DELETE", suffix="/item")
                else:
                    link_rule(get_link_to_many_collection)
                    link_rule(get_link_to_many_collection_count, suffix=":count")
                    link_rule(create_link_to_many_item, method="POST")
                    link_rule(update_link_to_many_item, method="PATCH", suffix="/<target_pk>")
                    link_rule(delete_link_to_many_item, method="DELETE", suffix="/<target_pk>")
                    link_rule(get_link_to_many_item_data, suffix="/<target_pk>:data")

        self._url_map = Map(url_map)
        self._debug = debug

    def __call__(self, environ, start_response):

        def _resp(data, status):
            resp = Response(json.dumps(data, indent=2 if self._debug else None), mimetype="application/json")
            if data is None:
                status = 204
            resp.status_code = status
            return resp(environ, start_response)

        try:
            urls = self._url_map.bind_to_environ(environ)
            endpoint, params = urls.match()
            rval = endpoint(Request(environ), **params)
            if isinstance(rval, Response):
                return rval(environ, start_response)
            else:
                rval, status = rval
                return _resp(rval, status)
        except errors.MultipleFound, e:
            return _resp(e.message, 500)  # this is actually a server problem
        except errors.ValidationError, e:
            return _resp(e.message, 400)
        except errors.DoesNotExist, e:
            return _resp(e.message, 404)
        except errors.DataConflictError, e:
            return _resp(e.message, 409)
        except errors.Forbidden, e:
            return _resp(e.message, 405)
        except errors.AuthorizationError, e:
            return _resp(e.message, 403)
        except NotImplementedError, e:
            return _resp(e.message, 501)
        except http_exceptions.HTTPException, e:
            return _resp(e.description, e.code)
        except Exception, e:
            logging.exception("Internal server error")
            if self._debug:
                msg = traceback.format_exc()
            else:
                msg = "Server error"
            return _resp(msg, 500)
