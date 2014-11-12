.. _descriptor:

Descriptor (schema)
===================

Descriptor is Resource API's way to notify the client about the structure of resources and relationships between them.

Lets say that there is the following collection of resources:

.. code-block:: python

    class User(Resource):
        """ Represents a person who uses the system """

        class Schema:
            email = StringField(regex="[^@]+@[^@]+\.[^@]+", pk=True)
            name = StringField(max_length=70, description="First name and last name")

        class Links:

            class cars(Link):
                """ All cars that belong to the user """
                target = "Car"
                related_name = "owner"

    class Car(Resource):
        """ The item being sold/bought within the system """

        class Schema:
            pk = IntegerField(pk=True, description="Integer identifier")
            model = StringField(description="E.g. BMW")
            brand = StringField(description="E.g. X6")
            year_of_production = DateTimeField(
                description="Time when the car was produced to estimate its age")

        class QuerySchema:
            age = IntegerField(description="Age of the car in years")

        class Links:

            class owner(Link):
                """ User who owns the car """
                target = "User"
                related_name = "cars"
                cardinality = Link.cardinalities.ONE
                master = True

                class Schema:
                    acquisition_data = DateTimeField(
                        description="Time when the car changed its owner")


And they are registered:

.. code-block:: python

    srv = Service()
    srv.register(User, "auth.User")
    srv.register(Car, "shop.Car")
    srv.setup()

In this case the descriptor shall look like:

.. code-block:: javascript

    {
       "shop.Car": {
           "pk_policy": {
               "description": " Uses value of a field marked as \"pk=True\" as resource's URI "
           },
           "description": " The item being sold/bought within the system ",
           "links": {
               "owner": {
                   "related_name": "cars",
                   "description": " User who owns the car ",
                   "required": false,
                   "target": "auth.User",
                   "cardinality": "ONE",
                   "schema": {
                       "acquisition_data": {
                           "type": "datetime",
                           "description": "Time when the car changed its owner"
                       }
                   }
               }
           },
           "schema": {
               "pk": {
                   "pk": true,
                   "type": "int",
                   "description": "Integer identifier"
               },
               "brand": {
                   "type": "string",
                   "description": "E.g. X6"
               },
               "model": {
                   "type": "string",
                   "description": "E.g. BMW"
               },
               "year_of_production": {
                   "type": "datetime",
                   "description": "Time when the car was produced to estimate its age"
               }
           },
           "query_schema": {
               "age": {
                   "type": "int",
                   "description": "Age of the car in years"
               }
           }
           }
       },
       "auth.User": {
           "pk_policy": {
               "description": " Uses value of a field marked as \"pk=True\" as resource's URI "
           },
           "description": " Represents a person who uses the system ",
           "links": {
               "cars": {
                   "related_name": "owner",
                   "description": " All cars that belong to the user ",
                   "required": false,
                   "target": "shop.Car",
                   "cardinality": "MANY",
                   "schema": {
                       "acquisition_data": {
                           "type": "datetime",
                           "description": "Time when the car changed its owner"
                       }
                   }
               }
           },
           "schema": {
               "email": {
                   "regex": "[^@]+@[^@]+\\.[^@]+",
                   "pk": true,
                   "type": "string",
                   "description": null
               },
               "name": {
                   "max_length": 70,
                   "type": "string",
                   "description": "First name and last name"
               }
           }
       }
   }

As it can be seen, the descriptor is a one to one mapping of the structure declared in python to JSON document.

There is a couple of things to note about the descriptor:

 - **description** fields are generated from resources'/links' docstrings and **description** argument of schema fields.
   If one of them is missing **description** is intentionally marked as *null*.
 - **target** corresponds to the name that was used when registering a specific resource
