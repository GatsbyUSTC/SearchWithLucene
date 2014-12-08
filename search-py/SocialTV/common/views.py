from django.shortcuts import render
import inspect


def generate_response(type, message):
    response_data = {}
    response_data['type'] = type
    response_data['module'] =  inspect.stack()[0][3]
    response_data['message'] = message
    return response_data
