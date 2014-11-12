from resource_api.interfaces import Resource, Link
from resource_api.schema import StringField, DateTimeField, IntegerField


class Student(Resource):
    """ A pupil """

    class Schema:
        email = StringField(regex="[^@]+@[^@]+\.[^@]+", pk=True,
                            description="Addess to which the notifications shall be sent")
        first_name = StringField(description="Given name(s)")
        last_name = StringField(description="Family name(s)")
        birthday = DateTimeField()

    class Links:

        class courses(Link):
            """ Courses the student has ever attended """

            class Schema:
                grade = IntegerField(min_val=1, max_val=5)

            target = "Course"
            related_name = "students"
            master = True

        class comments(Link):
            """ Comments made by the student """
            target = "Comment"
            related_name = "student"

        class ratings(Link):
            """ Ratings given by the student """
            target = "TeacherRating"
            related_name = "student"


class Teacher(Resource):
    """ A lecturer """

    class Schema:
        email = StringField(regex="[^@]+@[^@]+\.[^@]+", pk=True,
                            description="Addess to which the notifications shall be sent")
        first_name = StringField(description="Given name(s)")
        last_name = StringField(description="Family name(s)")
        category = StringField(description="TQS Category", choices=["four", "five", "five plus", "six"])

    class Links:

        class ratings(Link):
            """ Ratings given to the teacher """
            target = "TeacherRating"
            related_name = "teacher"

        class courses(Link):
            """ Courses the teacher is responsible for """
            target = "Course"
            related_name = "teacher"


class Course(Resource):
    """ An educational unit represinting the lessons for a specific set of topics """

    class Schema:
        name = StringField(pk=True, description="Name of the course. E.g. physics, maths.")
        duration = IntegerField(description="Length of the course in weeks")

    class Links:

        class teacher(Link):
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


class Comment(Resource):
    """ Student's comment about the course """

    class Schema:
        pk = StringField(pk=True, description="Identifier of the resource")
        value = StringField(description="Text of the comment")
        creation_time = DateTimeField(description="Time when the comment was added (for sorting purpose)")

    class Links:

        class student(Link):
            """ The pupil who made the comment """
            target = "Student"
            related_name = "comments"
            cardinality = Link.cardinalities.ONE
            master = True
            required = True

        class course(Link):
            """ The subject the comment was made about """
            target = "Course"
            related_name = "comments"
            cardinality = Link.cardinalities.ONE
            master = True
            required = True


class TeacherRating(Resource):
    """ Student's rating about teacher's performance """

    class Schema:
        pk = StringField(pk=True, description="Identifier of the resource")
        value = IntegerField(min_val=0, max_val=100, description="Lecturer's performance identifier ")
        creation_time = DateTimeField(description="Time when the rating was added (for sorting purpose)")

    class Links:

        class student(Link):
            """ The pupil who gave the rating to the teacher """
            target = "Student"
            related_name = "ratings"
            cardinality = Link.cardinalities.ONE
            master = True
            required = True

        class course(Link):
            """ The subject with respect to which the rating was given """
            target = "Course"
            related_name = "ratings"
            cardinality = Link.cardinalities.ONE
            master = True
            required = True

        class teacher(Link):
            """ The lecturer to whom the rating is related """
            target = "Teacher"
            related_name = "ratings"
            cardinality = Link.cardinalities.ONE
            master = True
            required = True
