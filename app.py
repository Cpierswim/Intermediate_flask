from flask import Flask, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_restful import Api, Resource
from dotenv import load_dotenv
from os import environ
from marshmallow import post_load, fields, ValidationError

load_dotenv()

# Create App instance
app = Flask(__name__)

# Add DB URI from .env
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('SQLALCHEMY_DATABASE_URI')

# Registering App w/ Services
db = SQLAlchemy(app)
ma = Marshmallow(app)
api = Api(app)
CORS(app)
Migrate(app, db)

# Creating student_course junction table
student_course = db.Table('student_course',
                    db.Column('student_id', db.Integer, db.ForeignKey('student.id')),
                    db.Column('course_id', db.Integer, db.ForeignKey('course.id')),
                    db.Column('grade', db.String(5))
                    )

# Models
class Student(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    year = db.Column(db.Integer())
    gpa = db.Column(db.Float())

class Course(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    instructor_id = db.Column(db.Integer(), db.ForeignKey('instructor.id'))
    credits = db.Column(db.Integer())
    instructor=db.relationship("Instructor")
    students = db.relationship("Student", secondary=student_course, backref='courses')

class Instructor(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    hire_date = db.Column(db.Date())



# Schemas
class StudentSchema(ma.Schema):
    id = fields.Integer(primary_key=True)
    first_name = fields.String(required=True)
    last_name = fields.String(required=True)
    year = fields.Integer()
    gpa = fields.Float()

    class Meta:
        fields = ("id", "first_name", "last_name", "year", "gpa")

class StudentNameSchema(ma.Schema):
    first_name = fields.String(required=True)
    last_name = fields.String(required=True)

    class Meta:
        fields = ("first_name", "last_name")

class InstructorSchema(ma.Schema):
    id = fields.Integer(primary_key=True)
    first_name = fields.String(required=True)
    last_name = fields.String(required=True)
    hire_date = fields.Date()
    class Meta:
        fields = ("id", "first_name", "last_name", "hire_date")

class CourseSchema(ma.Schema):
    id = fields.Integer(primary_key=True)
    name = fields.String(required=True)
    credits = fields.Integer()
    instructor = ma.Nested(InstructorSchema, many=False)
    students = ma.Nested(StudentNameSchema, many=True)
    class Meta:
        fields = ("id", "name", "credits", "instructor", "students")

students_schema = StudentSchema(many=True)
stuedents_name_schema = StudentNameSchema(many=True)

# Resources
class StudentListResoucre(Resource):
    def get(self):
        sort_param = request.args.get('order')
        print(sort_param)
        #sort_param = "last_name" if sort_param != "gpa" else sort_param  - if this is uncommented, it defaults to sorting by last_name

        query = Student.query
        if sort_param:
            if sort_param == "gpa":
                query = query.order_by(getattr(Student, "gpa").desc())
            else:
                query = query.order_by(sort_param)

        students = query.all()
        return students_schema.dump(students)
    
class FullCourseDetailResource(Resource):
    def get(self, course_id):
        course = Course.query.get_or_404(course_id)

        custom_response = {}
        custom_response["name"] = course.name
        custom_response["instructor_name"] = course.instructor.first_name + " " + course.instructor.last_name
        student_info_dictionary = {}
        student_info_dictionary["number_of_students"] = len(course.students)
        student_info_dictionary["students"] = stuedents_name_schema.dump(course.students)
        custom_response["student_info"] = student_info_dictionary

        return custom_response, 200


class InstructorListResource(Resource):
    pass

class CourseListResource(Resource):
    pass

class CourseResource(Resource):
    def get(self, course_id):
        pass

# Routes
api.add_resource(StudentListResoucre, "/api/students")
api.add_resource(FullCourseDetailResource, "/api/course_details/<int:course_id>")


