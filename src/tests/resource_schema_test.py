"""
Copyright (c) 2014-2015 F-Secure
See LICENSE for details
"""
import unittest
import json

from .sample_app.resources import Target, Source
from .simulators import TestService


EXPECTED_PY_SCHEMA = {
    "tests.sample_app.resources.Source": {
        "uri_policy": {
            "description": " Uses value of a field marked as \"pk=True\" as resource's URI ",
            "type": "pk_policy"
        },
        "meta": {
            "is_bar": False
        },
        "links": {
            "one_to_one_target": {
                "related_name": "one_to_one_source",
                "target": "tests.sample_app.resources.Target",
                "description": "Another link to just one target",
                "required": False,
                "changeable": True,
                "readonly": False,
                "cardinality": "ONE",
                "schema": {
                    "extra": {
                        "regex": None,
                        "min_length": None,
                        "description": None,
                        "default": None,
                        "required": False,
                        "choices": None,
                        "choice_labels": None,
                        "max_length": None,
                        "invalid_choices": None,
                        "type": "string"
                    },
                    "more_data": {
                        "regex": None,
                        "min_length": None,
                        "description": None,
                        "default": None,
                        "required": False,
                        "choices": None,
                        "choice_labels": None,
                        "max_length": None,
                        "invalid_choices": None,
                        "type": "string"
                    }
                }
            },
            "targets": {
                "related_name": "sources",
                "target": "tests.sample_app.resources.Target",
                "description": "Link to many targets",
                "required": False,
                "readonly": False,
                "meta": {
                    "hoster": "Nope"
                },
                "changeable": True,
                "cardinality": "MANY",
                "query_schema": {
                    "query_param": {
                        "regex": None,
                        "min_length": None,
                        "description": None,
                        "default": None,
                        "required": True,
                        "choices": None,
                        "choice_labels": None,
                        "max_length": None,
                        "invalid_choices": None,
                        "type": "string"
                    }
                },
                "schema": {
                    "extra": {
                        "regex": None,
                        "min_length": None,
                        "description": None,
                        "default": None,
                        "required": False,
                        "choices": None,
                        "choice_labels": None,
                        "max_length": None,
                        "invalid_choices": None,
                        "type": "string"
                    },
                    "more_data": {
                        "regex": None,
                        "min_length": None,
                        "description": None,
                        "default": None,
                        "required": False,
                        "choices": None,
                        "choice_labels": None,
                        "max_length": None,
                        "invalid_choices": None,
                        "type": "string"
                    }
                }
            },
            "the_target": {
                "related_name": "the_sources",
                "target": "tests.sample_app.resources.Target",
                "description": "Link to just one target",
                "required": False,
                "changeable": True,
                "readonly": False,
                "cardinality": "ONE",
                "schema": {
                    "extra": {
                        "regex": None,
                        "min_length": None,
                        "description": None,
                        "default": None,
                        "required": False,
                        "choices": None,
                        "choice_labels": None,
                        "max_length": None,
                        "invalid_choices": None,
                        "type": "string"
                    },
                    "more_data": {
                        "regex": None,
                        "min_length": None,
                        "description": None,
                        "default": None,
                        "required": False,
                        "choices": None,
                        "choice_labels": None,
                        "max_length": None,
                        "invalid_choices": None,
                        "type": "string"
                    }
                }
            }
        },
        "query_schema": {
            "query_param": {
                "regex": None,
                "min_length": None,
                "description": None,
                "default": None,
                "required": True,
                "choices": None,
                "choice_labels": None,
                "max_length": None,
                "invalid_choices": None,
                "type": "string"
            }
        },
        "schema": {
            "pk": {
                "min_val": None,
                "description": None,
                "default": None,
                "required": True,
                "choices": None,
                "choice_labels": None,
                "max_val": None,
                "pk": True,
                "invalid_choices": None,
                "type": "int"
            },
            "extra": {
                "regex": None,
                "min_length": None,
                "description": None,
                "default": None,
                "required": False,
                "choices": None,
                "choice_labels": None,
                "max_length": None,
                "invalid_choices": None,
                "type": "string"
            },
            "more_data": {
                "regex": None,
                "min_length": None,
                "description": None,
                "default": None,
                "required": False,
                "choices": None,
                "choice_labels": None,
                "max_length": None,
                "invalid_choices": None,
                "type": "string"
            }
        },
        "description": " Source Bar "
    },
    "tests.sample_app.resources.Target": {
        "uri_policy": {
            "description": " Uses value of a field marked as \"pk=True\" as resource's URI ",
            "type": "pk_policy"
        },
        "query_schema": {
            "query_param": {
                "regex": None,
                "min_length": None,
                "description": None,
                "default": None,
                "required": True,
                "choices": None,
                "choice_labels": None,
                "max_length": None,
                "invalid_choices": None,
                "type": "string"
            }
        },
        "description": " Target Foo ",
        "links": {
            "sources": {
                "related_name": "targets",
                "target": "tests.sample_app.resources.Source",
                "description": "Link to many sources",
                "required": False,
                "changeable": True,
                "cardinality": "MANY",
                "readonly": False,
                "query_schema": {
                    "query_param": {
                        "regex": None,
                        "min_length": None,
                        "description": None,
                        "default": None,
                        "required": True,
                        "choices": None,
                        "choice_labels": None,
                        "max_length": None,
                        "invalid_choices": None,
                        "type": "string"
                    }
                },
                "schema": {
                    "extra": {
                        "regex": None,
                        "min_length": None,
                        "description": None,
                        "default": None,
                        "required": False,
                        "choices": None,
                        "choice_labels": None,
                        "max_length": None,
                        "invalid_choices": None,
                        "type": "string"
                    },
                    "more_data": {
                        "regex": None,
                        "min_length": None,
                        "description": None,
                        "default": None,
                        "required": False,
                        "choices": None,
                        "choice_labels": None,
                        "max_length": None,
                        "invalid_choices": None,
                        "type": "string"
                    }
                }
            },
            "one_to_one_source": {
                "related_name": "one_to_one_target",
                "target": "tests.sample_app.resources.Source",
                "description": "Link to just one source",
                "required": False,
                "changeable": True,
                "cardinality": "ONE",
                "readonly": False,
                "schema": {
                    "extra": {
                        "regex": None,
                        "min_length": None,
                        "description": None,
                        "default": None,
                        "required": False,
                        "choices": None,
                        "choice_labels": None,
                        "max_length": None,
                        "invalid_choices": None,
                        "type": "string"
                    },
                    "more_data": {
                        "regex": None,
                        "min_length": None,
                        "description": None,
                        "default": None,
                        "required": False,
                        "choices": None,
                        "choice_labels": None,
                        "max_length": None,
                        "invalid_choices": None,
                        "type": "string"
                    }
                }
            },
            "the_sources": {
                "related_name": "the_target",
                "target": "tests.sample_app.resources.Source",
                "description": "Link to many sources as well",
                "required": False,
                "changeable": True,
                "cardinality": "MANY",
                "readonly": False,
                "schema": {
                    "extra": {
                        "regex": None,
                        "min_length": None,
                        "description": None,
                        "default": None,
                        "required": False,
                        "choices": None,
                        "choice_labels": None,
                        "max_length": None,
                        "invalid_choices": None,
                        "type": "string"
                    },
                    "more_data": {
                        "regex": None,
                        "min_length": None,
                        "description": None,
                        "default": None,
                        "required": False,
                        "choices": None,
                        "choice_labels": None,
                        "max_length": None,
                        "invalid_choices": None,
                        "type": "string"
                    }
                }
            }
        },
        "schema": {
            "pk": {
                "min_val": None,
                "description": None,
                "default": None,
                "required": True,
                "choices": None,
                "choice_labels": None,
                "max_val": None,
                "pk": True,
                "invalid_choices": None,
                "type": "int"
            },
            "extra": {
                "regex": None,
                "min_length": None,
                "description": None,
                "default": None,
                "required": False,
                "choices": None,
                "choice_labels": None,
                "max_length": None,
                "invalid_choices": None,
                "type": "string"
            },
            "more_data": {
                "regex": None,
                "min_length": None,
                "description": None,
                "default": None,
                "required": False,
                "choices": None,
                "choice_labels": None,
                "max_length": None,
                "invalid_choices": None,
                "type": "string"
            }
        }
    }
}


EXPECTED_HUMAN_SCHEMA = {
    "foo.Target": {
        "uri_policy": {
            "description": " Uses value of a field marked as \"pk=True\" as resource's URI ",
            "type": "pk_policy"
        },
        "query_schema": {
            "query_param": {
                "regex": None,
                "min_length": None,
                "description": None,
                "default": None,
                "required": True,
                "choices": None,
                "choice_labels": None,
                "max_length": None,
                "invalid_choices": None,
                "type": "string"
            }
        },
        "description": " Target Foo ",
        "links": {
            "sources": {
                "related_name": "targets",
                "target": "bar.Source",
                "description": "Link to many sources",
                "required": False,
                "changeable": True,
                "cardinality": "MANY",
                "readonly": False,
                "query_schema": {
                    "query_param": {
                        "regex": None,
                        "min_length": None,
                        "description": None,
                        "default": None,
                        "required": True,
                        "choices": None,
                        "choice_labels": None,
                        "max_length": None,
                        "invalid_choices": None,
                        "type": "string"
                    }
                },
                "schema": {
                    "extra": {
                        "regex": None,
                        "min_length": None,
                        "description": None,
                        "default": None,
                        "required": False,
                        "choices": None,
                        "choice_labels": None,
                        "max_length": None,
                        "invalid_choices": None,
                        "type": "string"
                    },
                    "more_data": {
                        "regex": None,
                        "min_length": None,
                        "description": None,
                        "default": None,
                        "required": False,
                        "choices": None,
                        "choice_labels": None,
                        "max_length": None,
                        "invalid_choices": None,
                        "type": "string"
                    }
                }
            },
            "one_to_one_source": {
                "related_name": "one_to_one_target",
                "target": "bar.Source",
                "description": "Link to just one source",
                "required": False,
                "changeable": True,
                "cardinality": "ONE",
                "readonly": False,
                "schema": {
                    "extra": {
                        "regex": None,
                        "min_length": None,
                        "description": None,
                        "default": None,
                        "required": False,
                        "choices": None,
                        "choice_labels": None,
                        "max_length": None,
                        "invalid_choices": None,
                        "type": "string"
                    },
                    "more_data": {
                        "regex": None,
                        "min_length": None,
                        "description": None,
                        "default": None,
                        "required": False,
                        "choices": None,
                        "choice_labels": None,
                        "max_length": None,
                        "invalid_choices": None,
                        "type": "string"
                    }
                }
            },
            "the_sources": {
                "related_name": "the_target",
                "target": "bar.Source",
                "description": "Link to many sources as well",
                "required": False,
                "changeable": True,
                "cardinality": "MANY",
                "readonly": False,
                "schema": {
                    "extra": {
                        "regex": None,
                        "min_length": None,
                        "description": None,
                        "default": None,
                        "required": False,
                        "choices": None,
                        "choice_labels": None,
                        "max_length": None,
                        "invalid_choices": None,
                        "type": "string"
                    },
                    "more_data": {
                        "regex": None,
                        "min_length": None,
                        "description": None,
                        "default": None,
                        "required": False,
                        "choices": None,
                        "choice_labels": None,
                        "max_length": None,
                        "invalid_choices": None,
                        "type": "string"
                    }
                }
            }
        },
        "schema": {
            "pk": {
                "min_val": None,
                "description": None,
                "default": None,
                "required": True,
                "choices": None,
                "choice_labels": None,
                "max_val": None,
                "pk": True,
                "invalid_choices": None,
                "type": "int"
            },
            "extra": {
                "regex": None,
                "min_length": None,
                "description": None,
                "default": None,
                "required": False,
                "choices": None,
                "choice_labels": None,
                "max_length": None,
                "invalid_choices": None,
                "type": "string"
            },
            "more_data": {
                "regex": None,
                "min_length": None,
                "description": None,
                "default": None,
                "required": False,
                "choices": None,
                "choice_labels": None,
                "max_length": None,
                "invalid_choices": None,
                "type": "string"
            }
        }
    },
    "bar.Source": {
        "uri_policy": {
            "description": " Uses value of a field marked as \"pk=True\" as resource's URI ",
            "type": "pk_policy"
        },
        "meta": {
            "is_bar": False
        },
        "links": {
            "one_to_one_target": {
                "related_name": "one_to_one_source",
                "target": "foo.Target",
                "description": "Another link to just one target",
                "required": False,
                "changeable": True,
                "cardinality": "ONE",
                "readonly": False,
                "schema": {
                    "extra": {
                        "regex": None,
                        "min_length": None,
                        "description": None,
                        "default": None,
                        "required": False,
                        "choices": None,
                        "choice_labels": None,
                        "max_length": None,
                        "invalid_choices": None,
                        "type": "string"
                    },
                    "more_data": {
                        "regex": None,
                        "min_length": None,
                        "description": None,
                        "default": None,
                        "required": False,
                        "choices": None,
                        "choice_labels": None,
                        "max_length": None,
                        "invalid_choices": None,
                        "type": "string"
                    }
                }
            },
            "targets": {
                "related_name": "sources",
                "target": "foo.Target",
                "description": "Link to many targets",
                "required": False,
                "readonly": False,
                "meta": {
                    "hoster": "Nope"
                },
                "changeable": True,
                "cardinality": "MANY",
                "query_schema": {
                    "query_param": {
                        "regex": None,
                        "min_length": None,
                        "description": None,
                        "default": None,
                        "required": True,
                        "choices": None,
                        "choice_labels": None,
                        "max_length": None,
                        "invalid_choices": None,
                        "type": "string"
                    }
                },
                "schema": {
                    "extra": {
                        "regex": None,
                        "min_length": None,
                        "description": None,
                        "default": None,
                        "required": False,
                        "choices": None,
                        "choice_labels": None,
                        "max_length": None,
                        "invalid_choices": None,
                        "type": "string"
                    },
                    "more_data": {
                        "regex": None,
                        "min_length": None,
                        "description": None,
                        "default": None,
                        "required": False,
                        "choices": None,
                        "choice_labels": None,
                        "max_length": None,
                        "invalid_choices": None,
                        "type": "string"
                    }
                }
            },
            "the_target": {
                "related_name": "the_sources",
                "target": "foo.Target",
                "description": "Link to just one target",
                "required": False,
                "changeable": True,
                "cardinality": "ONE",
                "readonly": False,
                "schema": {
                    "extra": {
                        "regex": None,
                        "min_length": None,
                        "description": None,
                        "default": None,
                        "required": False,
                        "choices": None,
                        "choice_labels": None,
                        "max_length": None,
                        "invalid_choices": None,
                        "type": "string"
                    },
                    "more_data": {
                        "regex": None,
                        "min_length": None,
                        "description": None,
                        "default": None,
                        "required": False,
                        "choices": None,
                        "choice_labels": None,
                        "max_length": None,
                        "invalid_choices": None,
                        "type": "string"
                    }
                }
            }
        },
        "query_schema": {
            "query_param": {
                "regex": None,
                "min_length": None,
                "description": None,
                "default": None,
                "required": True,
                "choices": None,
                "choice_labels": None,
                "max_length": None,
                "invalid_choices": None,
                "type": "string"
            }
        },
        "schema": {
            "pk": {
                "min_val": None,
                "description": None,
                "default": None,
                "required": True,
                "choices": None,
                "choice_labels": None,
                "max_val": None,
                "pk": True,
                "invalid_choices": None,
                "type": "int"
            },
            "extra": {
                "regex": None,
                "min_length": None,
                "description": None,
                "default": None,
                "required": False,
                "choices": None,
                "choice_labels": None,
                "max_length": None,
                "invalid_choices": None,
                "type": "string"
            },
            "more_data": {
                "regex": None,
                "min_length": None,
                "description": None,
                "default": None,
                "required": False,
                "choices": None,
                "choice_labels": None,
                "max_length": None,
                "invalid_choices": None,
                "type": "string"
            }
        },
        "description": " Source Bar "
    }
}


def compareDicts(dict_one, dict_two, cursor=""):
    processed_keys = set()
    for key, value in dict_one.iteritems():
        processed_keys.add(key)
        abs_path = cursor + "." + key
        if key not in dict_two:
            print "Extra node in dict_one %s" % abs_path
            continue
        elif isinstance(value, dict):
            other_value = dict_two[key]
            if not isinstance(other_value, dict):
                print "dict_two not a dict %s" % abs_path
                print other_value
                continue
            compareDicts(value, other_value, abs_path)
        elif value != dict_two[key]:
            print "Differ %s" % abs_path
            print "ONE"
            print value
            print "TWO"
            print dict_two[key]

    extra_nodes_in_dict_two = set(dict_two.keys()).difference(processed_keys)
    if extra_nodes_in_dict_two:
        for key in extra_nodes_in_dict_two:
            abs_path = cursor + "." + key
            print "Extra node in dict_two %s" % abs_path


class SchemaTest(unittest.TestCase):

    def test_schema(self):
        srv = TestService()
        srv.register(Target)
        srv.register(Source)
        srv.setup()

        val = json.dumps(srv.get_schema(human=False), indent=4)
        val = val.replace("false", "False")
        val = val.replace("true", "True")
        val = val.replace("null", "None")
        print val

        compareDicts(srv.get_schema(human=False), EXPECTED_PY_SCHEMA)
        self.assertEqual(srv.get_schema(human=False), EXPECTED_PY_SCHEMA)

    def test_human_schema(self):
        srv = TestService()
        srv.register(Target, "foo.Target")
        srv.register(Source, "bar.Source")
        srv.setup()

        val = json.dumps(srv.get_schema(), indent=4)
        val = val.replace("false", "False")
        val = val.replace("true", "True")
        val = val.replace("null", "None")

        compareDicts(srv.get_schema(), EXPECTED_HUMAN_SCHEMA)
        self.assertEqual(srv.get_schema(), EXPECTED_HUMAN_SCHEMA)
