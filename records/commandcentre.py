""""
    This is the command centre for all the commands created in the YA developer console
    This file contains the logic to understand a user message request from YA
    and return a response in the format of a YA message object accordingly

"""
from __future__ import print_function
import json
from pprint import pprint
import re
import requests
# from yellowant import YellowAnt
from yellowant.messageformat import MessageClass, MessageAttachmentsClass, AttachmentFieldsClass
from django.conf import settings
import victorops_client
from victorops_client.rest import ApiException
from .models import PipedriveUserToken, YellowUserToken


# The installation documentation for VictorOps API's python package can be found at
# https://github.com/honestbee/python-victorops/tree/master/python-client


class CommandCentre(object):
    """ Handles user commands
        Args:
            yellowant_user_id(int) : The user_id of the user
            yellowant_integration_id (int): The integration id of a YA user
            function_name (str): Invoke name of the command the user is calling
            args (dict): Any arguments required for the command to run
     """

    def __init__(self, yellowant_user_id, yellowant_integration_id, function_name, args):
        self.yellowant_user_id = yellowant_user_id
        self.yellowant_integration_id = yellowant_integration_id
        self.function_name = function_name
        self.args = args

    def parse(self):
        """
            Matching which function to call
        """
        self.commands = {
            'list_users': self.list_users,
            'search_users': self.search_users,
            'add_user': self.add_user,
            'add_deal': self.add_deal,
            'get_currencies': self.get_currencies,
        }

        self.user_integration = YellowUserToken.objects.get(yellowant_integration_id=self.yellowant_integration_id)
        self.pipedrive_object = PipedriveUserToken.objects.get(user_integration=self.user_integration)
        self.pipedrive_api_token = self.pipedrive_object.pipedrive_api_token
        self.headers = {
            'Content-Type': 'application/json',
            }
        return self.commands[self.function_name](self.args)

    def list_users(self,args):
        url = settings.PIPEDRIVE_LIST_ADD_USERS_URL + self.pipedrive_api_token
        response = requests.get(url, headers=self.headers)
        response_json = response.json()
        print(response_json)

        message = MessageClass()
        message.message_text = "Users"

        if not bool(response_json):
            attachment = MessageAttachmentsClass()
            attachment.text = "No users!"
            message.attach(attachment)
            return message.to_json()
        else:
            userinfo = response_json['data']
            for user in userinfo:
                attachment = MessageAttachmentsClass()

                field1 = AttachmentFieldsClass()
                field1.title = "Name"
                field1.value = user['name']
                attachment.attach_field(field1)

                field2 = AttachmentFieldsClass()
                field2.title = "ID"
                field2.value = user['id']
                attachment.attach_field(field2)

                field3 = AttachmentFieldsClass()
                field3.title = "Email"
                field3.value = user['email']
                attachment.attach_field(field3)

                field4 = AttachmentFieldsClass()
                field4.title = "Phone"
                field4.value = "-" if user['phone'] is None else user['phone']
                attachment.attach_field(field4)

                field5 = AttachmentFieldsClass()
                field5.title = "Default currency"
                field5.value = user['default_currency']
                attachment.attach_field(field5)

                field6 = AttachmentFieldsClass()
                field6.title = "Admin"
                field6.value = 'True' if user['is_admin'] else 'False'
                attachment.attach_field(field6)

                message.attach(attachment)

            return message.to_json()

    def search_users(self,args):
        message = MessageClass()

        if(len(args['Search-Term'])) < 2:
            attachment = MessageAttachmentsClass()
            attachment.text = "The search term must be at least 2 characters long"
            message.attach(attachment)
            return message.to_json()

        url = settings.PIPEDRIVE_SEARCH_USERS_URL%args['Search-Term'] + self.pipedrive_api_token
        print(url)

        body = {
            "term": args['Search-Term']
        }
        response = requests.get(url, headers=self.headers, data=json.dumps(body))
        response_json = response.json()
        print(response_json)

        message.message_text = "Users"
        userinfo = response_json['data']
        if userinfo is None:
            attachment = MessageAttachmentsClass()
            attachment.text = "No users found!"
            message.attach(attachment)
            return message.to_json()
        else:
            for user in userinfo:
                attachment = MessageAttachmentsClass()

                field1 = AttachmentFieldsClass()
                field1.title = "Name"
                field1.value = user['name']
                attachment.attach_field(field1)

                field2 = AttachmentFieldsClass()
                field2.title = "ID"
                field2.value = user['id']
                attachment.attach_field(field2)

                field3 = AttachmentFieldsClass()
                field3.title = "Email"
                field3.value = user['email']
                attachment.attach_field(field3)

                field4 = AttachmentFieldsClass()
                field4.title = "Phone"
                field4.value = "-" if user['phone'] is None else user['phone']
                attachment.attach_field(field4)

                field5 = AttachmentFieldsClass()
                field5.title = "Default currency"
                field5.value = user['default_currency']
                attachment.attach_field(field5)

                field6 = AttachmentFieldsClass()
                field6.title = "Admin"
                field6.value = 'True' if user['is_admin'] else 'False'
                attachment.attach_field(field6)

                message.attach(attachment)

            return message.to_json()

    def add_user(self, args):
        message = MessageClass()
        url = settings.PIPEDRIVE_LIST_ADD_USERS_URL + self.pipedrive_api_token
        body = {
                "name": args['Name'],
                "email": args['Email'],
                "active_flag": "1"
        }
        # POST request to pipedrive server
        response = requests.post(url, headers=self.headers, data=json.dumps(body))
        if response.status_code == 400:
            attachment = MessageAttachmentsClass()
            attachment.text = "Provided email not valid"
            message.attach(attachment)
            return message.to_json()
        else:
            response_json = response.json()
            print(response_json)
            userinfo = response_json['data']
            print(userinfo)
            message.message_text = "User Added!"
            attachment = MessageAttachmentsClass()

            field1 = AttachmentFieldsClass()
            field1.title = "Name"
            field1.value = userinfo['name']
            attachment.attach_field(field1)

            field2 = AttachmentFieldsClass()
            field2.title = "ID"
            field2.value = userinfo['id']
            attachment.attach_field(field2)

            field3 = AttachmentFieldsClass()
            field3.title = "Email"
            field3.value = userinfo['email']
            attachment.attach_field(field3)

            field4 = AttachmentFieldsClass()
            field4.title = "Phone"
            field4.value = "-" if userinfo['phone'] is None else userinfo['phone']
            attachment.attach_field(field4)

            field5 = AttachmentFieldsClass()
            field5.title = "Default currency"
            field5.value = userinfo['default_currency']
            attachment.attach_field(field5)

            field6 = AttachmentFieldsClass()
            field6.title = "Admin"
            field6.value = 'True' if userinfo['is_admin'] else 'False'
            attachment.attach_field(field6)

            message.attach(attachment)

            return message.to_json()

    def add_deal(self, args):
        url = settings.PIPEDRIVE_ADD_DEAL + self.pipedrive_api_token
        body = {
                "title": args['title'],
                "value": args['value'],
                "currency": "INR",
                "person_id": args['Contact-person-name'],
                "org_id": args['Organization-Name'],
                "status": "",
                "probability": args['Probability']
            }
        response = requests.post(url, headers=self.headers, data=json.dumps(body))
        # print(response)
        response_json = response.json()
        userinfo = response_json['data']

        message = MessageClass()
        message.message_text = "Deal created"

        attachment = MessageAttachmentsClass()

        field1 = AttachmentFieldsClass()
        field1.title = "Title"
        field1.value = userinfo['title']
        attachment.attach_field(field1)

        field2 = AttachmentFieldsClass()
        field2.title = "Value"
        field2.value = str(userinfo['currency']) + " " + str(userinfo['value'])
        attachment.attach_field(field2)

        field3 = AttachmentFieldsClass()
        field3.title = "Name"
        field3.value = userinfo['person_id']['name']
        attachment.attach_field(field3)

        field4 = AttachmentFieldsClass()
        field4.title = "Company"
        field4.value = userinfo['org_id']['name']
        attachment.attach_field(field4)

        field5 = AttachmentFieldsClass()
        field5.title = "Handled by"
        field5.value = userinfo['user_id']['name']
        attachment.attach_field(field5)

        message.attach(attachment)
        return message.to_json()

    def get_currencies(self, args):
        pass


