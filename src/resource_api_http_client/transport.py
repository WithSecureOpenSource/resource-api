"""
Copyright (c) 2014-2015 F-Secure
See LICENSE for details
"""
import json

from datetime import datetime
import isodate

import requests

from resource_api.errors import ValidationError, DoesNotExist, AuthorizationError, DataConflictError, Forbidden


EXCEPTION_MAP = {
    400: ValidationError,
    403: AuthorizationError,
    404: DoesNotExist,
    405: Forbidden,
    409: DataConflictError,
    501: NotImplementedError
}


class Response(object):

    def __init__(self, status_code, data):
        self.status_code, self.data = status_code, data


class HttpClient(object):

    def __init__(self, auth_headers=None, session=None):
        self._auth_headers = auth_headers or {}
        self._session = session or requests.Session()

    def open(self, path, method="GET", content_type="application/json", query_string=None, data=None):
        headers = {'content-type': content_type}
        headers.update(self._auth_headers)
        resp = self._session.request(url=path, method=method.lower(), params=query_string, data=data, headers=headers)
        if resp.content:
            data = resp.text
        else:
            data = None
        return Response(resp.status_code, data)


class JSONEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return None


class JSONDecoder(json.JSONDecoder):

    def __init__(self, schema=None, *args, **kwargs):
        super(JSONDecoder, self).__init__(*args, **kwargs)
        self.schema = schema

    def decode(self, string):
        json_obj = super(JSONDecoder, self).decode(string)
        return self._decode_obj(json_obj)

    def _decode_obj(self, json_obj):
        if self.schema and isinstance(json_obj, dict):
            py_obj = self._decode_dict(json_obj, self.schema)
        elif self.schema and isinstance(json_obj, list):
            py_obj = map(self._decode_obj, json_obj)
        else:
            py_obj = json_obj

        return py_obj

    def _decode_dict(self, json_dict, schema=None):
        py_dict = {}
        for name, value in json_dict.items():
            field_schema = schema.get(name, {}) if schema else {}
            if isinstance(value, dict):
                py_dict[name] = self._decode_dict(value, field_schema)
            elif field_schema.get("type") == "datetime":
                py_dict[name] = isodate.parse_datetime(value)
            else:
                py_dict[name] = value

        return py_dict


class JsonClient(object):

    def __init__(self, http_client):
        self._http_client = http_client

    def open(self, url, method="GET", params=None, data=None, schema=None):

        if data is not None:
            data = json.dumps(data, cls=JSONEncoder)

        if params is not None:
            for key, value in params.iteritems():
                if isinstance(value, list) or isinstance(value, dict):
                    params[key] = json.dumps(value, cls=JSONEncoder)

        if not url:
            url += "/"

        resp = self._http_client.open(
            path=url,
            method=method,
            content_type="application/json",
            query_string=params,
            data=data
        )

        rval = json.loads(resp.data, cls=JSONDecoder, schema=schema) if resp.data else None

        if resp.status_code > 199 and resp.status_code < 400:
            return rval

        exception_class = EXCEPTION_MAP.get(resp.status_code, Exception)

        raise exception_class(rval)
