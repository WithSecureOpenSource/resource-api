import shelve
import os
import re

from resource_api.interfaces import Resource as BaseResource, Link as BaseLink, AbstractUriPolicy
from resource_api.schema import StringField, DateTimeField, IntegerField
from resource_api.service import Service
from resource_api.errors import ValidationError


RE_SHA1 = re.compile("^[a-f0-9]{40}$")
SHELVE_PATH = "/tmp/school.shelve.db"


class User(object):

    def __init__(self, email=None):

        if email is None:
            self.is_anonymous = True
        else:
            self.is_anonymous = False

        if email == "admin@school.com":
            self.is_admin = True
        else:
            self.is_admin = False

        self.email = email


class ShelveService(Service):

    def __init__(self):
        super(ShelveService, self).__init__()
        self._storage = shelve.open(SHELVE_PATH, writeback=True)

    def _get_context(self):
        return {"storage": self._storage, "service": self}

    def _get_user(self, data):
        if data is None:
            return User(None)
        else:
            return User(data.get("email"))

    def __del__(self):
        self._storage.close()


class Resource(BaseResource):

    def __init__(self, context):
        super(Resource, self).__init__(context)
        self._storage = context["storage"]

    def exists(self, user, pk):
        return pk in self._storage.get(self.get_name(), {})

    def get_data(self, user, pk):
        return self._storage.get(self.get_name(), {}).get(pk)

    def delete(self, user, pk):
        self._storage.get(self.get_name(), {}).pop(pk)
        self._storage.sync()

    def create(self, user, pk, data):
        if self.get_name() not in self._storage:
            self._storage[self.get_name()] = {}
        self._storage[self.get_name()][pk] = data
        self._storage.sync()

    def update(self, user, pk, data):
        self._storage[self.get_name()][pk].update(data)
        self._storage.sync()

    def get_uris(self, user, params=None):
        return self._storage.get(self.get_name(), {}).keys()

    def get_count(self, user, params=None):
        return len(self.get_uris(params))

    def can_get_data(self, user, pk, data):
        """ Only authenticated users can access data """
        if user.is_anonymous:
            return False
        else:
            return True

    def can_get_uris(self, user):
        """ Only authenticated users can access data """
        if user.is_anonymous:
            return False
        else:
            return True


class Link(BaseLink):

    def __init__(self, context):
        super(Link, self).__init__(context)
        self._storage = context["storage"]

    def exists(self, user, pk, rel_pk):
        return rel_pk in self._storage.get((pk, self.get_name()), {})

    def get_data(self, user, pk, rel_pk):
        return self._storage.get((pk, self.get_name()), {}).get(rel_pk)

    def create(self, user, pk, rel_pk, data=None):
        key = (pk, self.get_name())
        if key not in self._storage:
            self._storage[key] = {}
        self._storage[key][rel_pk] = data
        self._storage.sync()

    def update(self, user, pk, rel_pk, data):
        self._storage[key][rel_pk].update(data)
        self._storage.sync()

    def delete(self, user, pk, rel_pk):
        self._storage.get((pk, self.get_name()), {}).pop(rel_pk)
        self._storage.sync()

    def get_uris(self, user, pk, params=None):
        return self._storage.get((pk, self.get_name()), {}).keys()

    def get_count(self, user, pk, params=None):
        return len(self.get_uris(pk, params))

    def can_get_data(self, user, pk, rel_pk, data):
        """ Only authenticated users can access data """
        if user.is_anonymous:
            return False
        else:
            return True

    def can_get_uris(self, user, pk):
        """ Only authenticated users can access data """
        if user.is_anonymous:
            return False
        else:
            return True


class Person(Resource):

    class Schema:
        email = StringField(regex="[^@]+@[^@]+\.[^@]+", pk=True,
                            description="Addess to which the notifications shall be sent")
        first_name = StringField(description="Given name(s)")
        last_name = StringField(description="Family name(s)")

    def can_update(self, user, pk):
        """ Only a person himself can update his own information """
        return user.email == pk or user.is_admin

    def can_delete(self, user, pk):
        """ Only admins can delete people """
        return user.is_admin


class Student(Person):
    """ A pupil """

    class Schema(Person.Schema):
        birthday = DateTimeField()

    class Links:

        class courses(Link):
            """ Courses the student has ever attended """

            target = "Course"
            related_name = "students"
            master = True

            class Schema:
                grade = IntegerField(min_val=1, max_val=5)

            def _is_course_teacher(self, user, pk, rel_pk):
                """ Only teachers can add/remove students to/from courses and grade them.

                And they can do it with their courses ONLY.
                """
                if user.is_admin:
                    return True
                teacher_data = self._storage.get(Teacher.get_name(), {}).get(user.email)
                if teacher_data is None:
                    return False
                else:
                    teacher_courses = self._storage.get((user.email, Teacher.Links.courses.get_name()), {})
                    return rel_pk in teacher_courses

            def can_create(self, user, pk, rel_pk, data=None):
                return self._is_course_teacher(user, pk, rel_pk)

            can_update = can_create
            can_delete = _is_course_teacher

        class comments(Link):
            """ Comments made by the student """
            target = "Comment"
            related_name = "student"

        class ratings(Link):
            """ Ratings given by the student """
            target = "TeacherRating"
            related_name = "student"


class Teacher(Person):
    """ A lecturer """

    class Schema(Person.Schema):
        category = StringField(description="TQS Category",
                               choices=["four", "five", "five plus", "six"])

    class Links:

        class ratings(Link):
            """ Ratings given to the teacher """
            target = "TeacherRating"
            related_name = "teacher"

        class courses(Link):
            """ Courses the teacher is responsible for """
            target = "Course"
            related_name = "teacher"



class PersonalLink(Link):
    """ Users can link things to their accounts only """

    def can_update(self, user, pk, rel_pk, data):
        return user.email == rel_pk or user.is_admin

    def can_create(self, user, pk, rel_pk, data):
        return user.email == rel_pk or user.is_admin

    def can_delete(self, user, pk, rel_pk):
        return user.email == rel_pk or user.is_admin



class Course(Resource):
    """ An educational unit represinting the lessons for a specific set of topics """

    class Schema:
        name = StringField(pk=True, description="Name of the course. E.g. physics, maths.")
        duration = IntegerField(description="Length of the course in weeks")

    class Links:

        class teacher(PersonalLink):
            """ The lecturer of the course """
            target = "Teacher"
            related_name = "courses"
            cardinality = Link.cardinalities.ONE
            master = True
            required = True

        class comments(Link):
            """ All comments made about the course """
            target = "Comment"
            related_name = "course"

        class ratings(Link):
            """ All ratings that were given to the teachers of the specific course """
            target = "TeacherRating"
            related_name = "course"

        class students(Link):
            """ All pupils who attend the course """
            target = "Student"
            related_name = "courses"


class AutoGenSha1UriPolicy(AbstractUriPolicy):
    """ Uses a randomly generated sha1 as a primary key """

    @property
    def type(self):
        return "autogen_policy"

    def generate_pk(self, data):
        return os.urandom(16).encode('hex')

    def serialize(self, pk):
        return pk

    def deserialize(self, pk):
        if not isinstance(pk, basestring):
            raise ValidationError("Has to be string")
        if not RE_SHA1.match(value):
            raise ValidationError("PK is not a valid SHA1")
        return pk


class Comment(Resource):
    """ Student's comment about the course """

    UriPolicy = AutoGenSha1UriPolicy

    class Schema:
        pk = StringField(pk=True, description="Identifier of the resource")
        value = StringField(description="Text of the comment")
        creation_time = DateTimeField(description="Time when the comment was added (for sorting purpose)")

    class Links:

        class student(PersonalLink):
            """ The pupil who made the comment """
            target = "Student"
            related_name = "comments"
            cardinality = Link.cardinalities.ONE
            master = True
            required = True

            def can_delete(self, user, pk, rel_pk):
                """ It does not make any sense to let anyone touch the comment's student once it is created """
                return False

        class course(Link):
            """ The subject the comment was made about """
            target = "Course"
            related_name = "comments"
            cardinality = Link.cardinalities.ONE
            master = True
            required = True

            def can_delete(self, user, pk, rel_pk):
                """ It does not make any sense to let anyone touch the comment's course once it is created """
                return False


class TeacherRating(Resource):
    """ Student's rating about teacher's performance """

    UriPolicy = AutoGenSha1UriPolicy

    class Schema:
        pk = StringField(pk=True, description="Identifier of the resource")
        value = IntegerField(min_val=0, max_val=100, description="Lecturer's performance identifier ")
        creation_time = DateTimeField(description="Time when the rating was added (for sorting purpose)")

    class Links:

        class student(PersonalLink):
            """ The pupil who gave the rating to the teacher """
            target = "Student"
            related_name = "ratings"
            cardinality = Link.cardinalities.ONE
            master = True
            required = True

            def can_delete(self, user, pk, rel_pk):
                """ It does not make any sense to let anyone touch the rating's student once it is created """
                return False

        class course(Link):
            """ The subject with respect to which the rating was given """
            target = "Course"
            related_name = "ratings"
            cardinality = Link.cardinalities.ONE
            master = True
            required = True

            def can_delete(self, user, pk, rel_pk):
                """ It does not make any sense to let anyone touch the ratings's course once it is created """
                return False

        class teacher(Link):
            """ The lecturer to whom the rating is related """
            target = "Teacher"
            related_name = "ratings"
            cardinality = Link.cardinalities.ONE
            master = True
            required = True

            def can_delete(self, user, pk, rel_pk):
                """ It does not make any sense to let anyone touch the rating's teacher once it is created """
                return False


srv = ShelveService()
srv.register(Student, "school.Student")
srv.register(Teacher, "school.Teacher")
srv.register(Course, "school.Course")
srv.register(Comment, "school.Comment")
srv.register(TeacherRating, "school.TeacherRating")


from resource_api_http.http import Application
from werkzeug.serving import run_simple
app = Application(srv)
run_simple('localhost', 8080, app, use_reloader=True)
