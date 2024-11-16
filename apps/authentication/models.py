# -*- encoding: utf-8 -*-

from flask_login import UserMixin
from apps import db, login_manager
from apps.authentication.util import hash_pass
from datetime import datetime
import pickle
from sqlalchemy.types import PickleType

class Users(db.Model, UserMixin):
    __tablename__ = 'Users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    email = db.Column(db.String(64), unique=True)
    password = db.Column(db.LargeBinary)
    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]
            if property == 'password':
                value = hash_pass(value)  # we need bytes here (not plain str)
            setattr(self, property, value)
    def __repr__(self):
        return str(self.username)

class Upload_Case(db.Model, UserMixin):
    __tablename__ = 'UploadFiles'
    id = db.Column(db.Integer, primary_key = True)
    user = db.Column(db.Text)
    analyst = db.Column(db.Text)
    case_number = db.Column(db.Text)
    description = db.Column(db.Text)
    file = db.Column(db.Text)
    normalization = db.Column(db.Text)

class Normalization(db.Model, UserMixin) :
    __tablename__ = "Normalization"
    id = db.Column(db.Integer, primary_key = True)
    normalization_definition = db.Column(db.Integer)
    file = db.Column(db.Text)
    result = db.Column(db.Text)
    artifacts_names = db.Column(db.Text)

class GraphData(db.Model, UserMixin):
    __tablename__ = "GraphData"
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.String(50), nullable=False)
    graph_data = db.Column(db.JSON, nullable=False)
    query_data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, case_id, graph_data, query_data):
        self.case_id = case_id
        self.graph_data = graph_data
        self.query_data = query_data

class UsbData(db.Model, UserMixin) :
    __tablename__ = "UsbData"
    id = db.Column(db.Integer, primary_key = True)
    case_id = db.Column(db.Text)
    usb_data = db.Column(db.JSON)

class FilteringData(db.Model, UserMixin) :
    __tablename__ = "FilteringData"
    id = db.Column(db.Integer, primary_key = True)
    case_id = db.Column(db.Text)
    start_time = db.Column(db.Text)
    end_time = db.Column(db.Text)
    filtering_data = db.Column(db.JSON)
    datas = db.Column(PickleType)

class PromptQuries(db.Model, UserMixin) :
    __tablename__ = "PromptQuries"
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.Text)
    case_id = db.Column(db.Text)
    query = db.Column(db.Text)
    tables = db.Column(db.Text)
    response = db.Column(db.Text)
    graph_index = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.now)

class GroupParsingProcess(db.Model, UserMixin) :
    __tablename__ = "GroupParsingProcess"
    id = db.Column(db.Integer, primary_key = True)
    case_id = db.Column(db.Text)
    result = db.Column(db.Integer)
    output_path = db.Column(db.Text)

class GroupParingResults(db.Model, UserMixin) :
    __tablename__ = "GroupParingResults"
    id = db.Column(db.Integer, primary_key = True)
    case_id = db.Column(db.Text)
    logTagger_output_path = db.Column(db.Text)
    result1 = db.Column(db.JSON)
    result2 = db.Column(db.JSON)
    result3 = db.Column(db.JSON)
    result4 = db.Column(db.JSON)

class PrinterData_final(db.Model, UserMixin) :
    __tablename__ = "PrinterData_final"
    id = db.Column(db.Integer, primary_key = True)
    case_id = db.Column(db.Text)
    printer_data = db.Column(db.JSON)

class UsbData_final(db.Model, UserMixin) :
    __tablename__ = "UsbData_final"
    id = db.Column(db.Integer, primary_key = True)
    case_id = db.Column(db.Text)
    usb_data = db.Column(db.JSON)

class Analyzed_file_list(db.Model, UserMixin) :
    __tablename__ = "Analyzed_file_list"
    id = db.Column(db.Integer, primary_key = True)
    case_id = db.Column(db.Text)
    data = db.Column(db.JSON)

class Mail_final(db.Model, UserMixin) :
    __tablename__ = "Mail_final"
    id = db.Column(db.Integer, primary_key = True)
    case_id = db.Column(db.Text)
    mail_data = db.Column(db.JSON)
    


@login_manager.user_loader
def user_loader(id):
    return Users.query.filter_by(id=id).first()


@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    user = Users.query.filter_by(username=username).first()
    return user if user else None
