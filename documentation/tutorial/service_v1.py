from resource_api.interfaces import Resource, Link


class Student(Resource):
    """ A pupil """

    class Links:

        class courses(Link):
            """ Courses the student has ever attended """
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
