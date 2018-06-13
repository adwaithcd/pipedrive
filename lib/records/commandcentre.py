""""
    This is the command centre for all the commands created in the YA developer console
    This file contains the logic to understand a user message request from YA
    and return a response in the format of a YA message object accordingly

"""
from __future__ import print_function
import json
import requests
# from yellowant import YellowAnt
from yellowant.messageformat import MessageClass, MessageAttachmentsClass, AttachmentFieldsClass
from django.conf import settings
from .models import PipedriveUserToken, YellowUserToken


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
            'list_all_deals': self.list_all_deals,
            'activity_type': self.activity_type,
            'add_activity': self.add_activity,
            'list_pipelines': self.list_pipelines,
            'add_pipeline': self.add_pipeline,
            'probability_list': self.probability_list,
            'list_activities': self.list_activities
        }

        self.user_integration = YellowUserToken.objects.get(yellowant_integration_id=self.yellowant_integration_id)
        self.pipedrive_object = PipedriveUserToken.objects.get(user_integration=self.user_integration)
        self.pipedrive_api_token = self.pipedrive_object.pipedrive_api_token
        self.headers = {
            'Content-Type': 'application/json',
            }
        return self.commands[self.function_name](self.args)

    def list_users(self, args):
        """
            Returns data about all users within the company
        """
        url = settings.PIPEDRIVE_LIST_ADD_USERS_URL + self.pipedrive_api_token
        response = requests.get(url, headers=self.headers)
        response_json = response.json()
        # print(response_json)

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

    def search_users(self, args):
        """
           Finds users by their name.The input must be at least 2 characters long.
        """
        message = MessageClass()

        if(len(args['Search-Term'])) < 2:
            attachment = MessageAttachmentsClass()
            attachment.text = "The search term must be at least 2 characters long"
            message.attach(attachment)
            return message.to_json()

        url = settings.PIPEDRIVE_SEARCH_USERS_URL%args['Search-Term'] + self.pipedrive_api_token
        # print(url)

        body = {
            "term": args['Search-Term']
        }
        response = requests.get(url, headers=self.headers, data=json.dumps(body))
        response_json = response.json()
        # print(response_json)

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
        """
            Adds a new user to the company, returns the ID upon success.
        """
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
            # print(response_json)
            userinfo = response_json['data']
            # print(userinfo)
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

            phone = "-" if userinfo['phone'] is None else userinfo['phone']

            message.data = {
                "name": userinfo['name'],
                "ID": userinfo['id'],
                "Email": userinfo['email'],
                "Phone": phone,
                "Default currency": userinfo['default_currency']
            }

            message.attach(attachment)
            return message.to_json()

    def add_deal(self, args):
        """
            Adds a new deal.
        """
        url = settings.PIPEDRIVE_ADD_DEAL + self.pipedrive_api_token
        body = {
            "title": args['title'],
            "value": args['value'],
            "currency": args['currency'],
            "person_id": args['Contact-person-name'],
            "org_id": args['Organization-Name'],
            "status": "",
        }
        response = requests.post(url, headers=self.headers, data=json.dumps(body))
        # print(response)
        message = MessageClass()

        if response.status_code == 400:
            attachment = MessageAttachmentsClass()
            attachment.text = "No stages found in the default pipeline. Cannot add a deal."
            message.attach(attachment)
            return message.to_json()
        else:
            response_json = response.json()
            dealinfo = response_json['data']
            message.message_text = "Deal created"

            attachment = MessageAttachmentsClass()

            field1 = AttachmentFieldsClass()
            field1.title = "Title"
            field1.value = dealinfo['title']
            attachment.attach_field(field1)

            field2 = AttachmentFieldsClass()
            field2.title = "Value"
            field2.value = str(dealinfo['currency']) + " " + str(dealinfo['value'])
            attachment.attach_field(field2)

            field3 = AttachmentFieldsClass()
            field3.title = "Name"
            field3.value = dealinfo['person_id']['name']
            attachment.attach_field(field3)

            field4 = AttachmentFieldsClass()
            field4.title = "Company"
            field4.value = dealinfo['org_id']['name']
            attachment.attach_field(field4)

            field5 = AttachmentFieldsClass()
            field5.title = "Handled by"
            field5.value = dealinfo['user_id']['name']
            attachment.attach_field(field5)

            message.data = {
                "Title": dealinfo['title'],
                "Value": dealinfo['value'],
                "Currency": dealinfo['currency'],
                "Name": dealinfo['person_id']['name'],
                "Company": dealinfo['org_id']['name'],
                "Handled by": dealinfo['user_id']['name']
            }

            message.attach(attachment)
            return message.to_json()

    def get_currencies(self, args):
        """
            This is a picklist function which returns all the available currencies
        """
        url = settings.PIPEDRIVE_GET_CURRENCY + self.pipedrive_api_token
        response = requests.get(url, headers=self.headers)
        response_json = response.json()
        # print(response_json)
        message = MessageClass()
        message.message_text = "Currency list:"
        data = response_json['data']
        name_list = {'data': []}
        for i in data:
            name_list['data'].append({"code": str(i['code']), "name": str(i['name'])})
        message.data = name_list
        # print(message.data)
        return message.to_json()

    def list_all_deals(self, args):
        """
            Returns all deals
        """
        url = settings.PIPEDRIVE_GET_ALL_DEAL + self.pipedrive_api_token
        response = requests.get(url, headers=self.headers)
        response_json = response.json()
        # print(response_json)
        deal_info = response_json['data']

        message = MessageClass()
        message.message_text = "Deals"

        for i in range(len(deal_info)):
            attachment = MessageAttachmentsClass()
            attachment.text = "Deal" + " " + str(i+1)

            field1 = AttachmentFieldsClass()
            field1.title = "Title"
            field1.value = deal_info[i]['title']
            attachment.attach_field(field1)

            field2 = AttachmentFieldsClass()
            field2.title = "Value"
            field2.value = str(deal_info[i]['currency']) + " " + str(deal_info[i]['value'])
            attachment.attach_field(field2)

            field3 = AttachmentFieldsClass()
            field3.title = "Name"
            field3.value = deal_info[i]['person_id']['name']
            attachment.attach_field(field3)

            field4 = AttachmentFieldsClass()
            field4.title = "Company"
            field4.value = deal_info[i]['org_id']['name']
            attachment.attach_field(field4)

            field5 = AttachmentFieldsClass()
            field5.title = "Handled by"
            field5.value = deal_info[i]['user_id']['name']
            attachment.attach_field(field5)

            field6 = AttachmentFieldsClass()
            field6.title = "Status"
            field6.value = deal_info[i]['status']
            attachment.attach_field(field6)

            message.attach(attachment)
        return message.to_json()

    def activity_type(self, args):
        """
            This is a picklist function which returns all the various activity types
        """
        message = MessageClass()
        data = {'list': []}
        data['list'].append({"activity": "Call"})
        data['list'].append({"activity": "Meeting"})
        data['list'].append({"activity": "Task"})
        data['list'].append({"activity": "Deadline"})
        data['list'].append({"activity": "Email"})
        data['list'].append({"activity": "Lunch"})
        # print(data)
        message.data = data
        return message.to_json()

    def add_activity(self, args):
        """
            Adds a new activity.
        """
        url = settings.PIPEDRIVE_ADD_ACTIVITY + self.pipedrive_api_token
        body = {
            "subject": args['Subject'],
            "done": "0",
            "type": args['Type'],
            "due_date": args['Due-Date'],
            "deal_id": args['Deal'],
            "person_id": args['Contact-Person']
        }
        response = requests.post(url, headers=self.headers, data=json.dumps(body))
        # print(response)
        # print(response_json)
        message = MessageClass()
        if response.status_code == 400:
            attachment = MessageAttachmentsClass()
            attachment.text = "Unrecognized date value for due date."
            message.attach(attachment)
            return message.to_json()
        else:
            response_json = response.json()
            activity_info = response_json['data']
            message.message_text = "Activity added"

            attachment = MessageAttachmentsClass()

            field1 = AttachmentFieldsClass()
            field1.title = "Activity Subject"
            field1.value = activity_info['subject']
            attachment.attach_field(field1)

            field2 = AttachmentFieldsClass()
            field2.title = "Activity Type"
            field2.value = activity_info['type']
            attachment.attach_field(field2)

            field3 = AttachmentFieldsClass()
            field3.title = "Due Date"
            field3.value = activity_info['due_date']
            attachment.attach_field(field3)

            field4 = AttachmentFieldsClass()
            field4.title = "Contact Person"
            field4.value = activity_info['person_name']
            attachment.attach_field(field4)

            field5 = AttachmentFieldsClass()
            field5.title = "Company"
            field5.value = activity_info['org_name']
            attachment.attach_field(field5)

            field6 = AttachmentFieldsClass()
            field6.title = "Handled by"
            field6.value = activity_info['owner_name']
            attachment.attach_field(field6)

            message.data = {
                "Activity Subject": activity_info['subject'],
                "Activity Type": activity_info['type'],
                "Due Date": activity_info['due_date'],
                "Contact Person": activity_info['person_name'],
                "Company": activity_info['org_name'],
                "Handled by": activity_info['owner_name']
            }

            message.attach(attachment)
            return message.to_json()

    def list_pipelines(self, args):
        """
            Returns data about all pipelines
        """
        url = settings.PIPEDRIVE_GET_ADD_PIPELINE + self.pipedrive_api_token
        response = requests.get(url, headers=self.headers)
        response_json = response.json()
        # print(response_json)
        pipeline_info = response_json['data']
        # print(deal_info)
        message = MessageClass()
        message.message_text = "Pipelines"
        for i in range(len(pipeline_info)):
            attachment = MessageAttachmentsClass()
            attachment.text = "Pipeline" + " " + str(i+1)

            field1 = AttachmentFieldsClass()
            field1.title = "Name"
            field1.value = pipeline_info[i]['name']
            attachment.attach_field(field1)

            field2 = AttachmentFieldsClass()
            field2.title = "Url title"
            field2.value = pipeline_info[i]['url_title']
            attachment.attach_field(field2)

            field3 = AttachmentFieldsClass()
            field3.title = "Add Time"
            field3.value = pipeline_info[i]['add_time']
            attachment.attach_field(field3)

            field4 = AttachmentFieldsClass()
            field4.title = "Order"
            field4.value = pipeline_info[i]['order_nr']
            attachment.attach_field(field4)

            message.attach(attachment)
        return message.to_json()

    def probability_list(self, args):
        """
            This is a picklist function which gives two options.
            1 - Enable Probability
            0 - Disable Probability
        """
        message = MessageClass()
        data = {'list': []}
        data['list'].append({"probability": 0})
        data['list'].append({"probability": 1})
        # print(data)
        message.data = data
        return message.to_json()

    def add_pipeline(self, args):
        """
            Adds a new pipeline
        """
        url = settings.PIPEDRIVE_GET_ADD_PIPELINE + self.pipedrive_api_token
        body = {
            "name": args['Name'],
            "deal_probability": args['Deal-Probability'],
            "active": "1"
        }
        response = requests.post(url, headers=self.headers, data=json.dumps(body))
        # print(response.text)
        message = MessageClass()

        if response.status_code == 400:
            attachment = MessageAttachmentsClass()
            attachment.text = "Cannot add the pipeline."
            message.attach(attachment)
            return message.to_json()
        else:
            response_json = response.json()
            pipeline_info = response_json['data']
            message.message_text = "Pipeline created"

            attachment = MessageAttachmentsClass()

            field1 = AttachmentFieldsClass()
            field1.title = "Name"
            field1.value = pipeline_info['name']
            attachment.attach_field(field1)

            field2 = AttachmentFieldsClass()
            field2.title = "Url title"
            field2.value = pipeline_info['url_title']
            attachment.attach_field(field2)

            field3 = AttachmentFieldsClass()
            field3.title = "Add Time"
            field3.value = pipeline_info['add_time']
            attachment.attach_field(field3)

            field4 = AttachmentFieldsClass()
            field4.title = "Order"
            field4.value = pipeline_info['order_nr']
            attachment.attach_field(field4)

            field5 = AttachmentFieldsClass()
            field5.title = "Deal Probability"
            field5.value = pipeline_info['deal_probability']
            attachment.attach_field(field5)

            message.data = {
                "Name": pipeline_info['name'],
                "Url title": pipeline_info['url_title'],
                "Add Time": pipeline_info['add_time'],
                "Order": pipeline_info['order_nr']
            }

            message.attach(attachment)
            return message.to_json()

    def list_activities(self, args):
        """
            Returns all activities assigned to a particular user
        """
        url = settings.PIPEDRIVE_GET_ALL_ACTIVITY + self.pipedrive_api_token
        response = requests.get(url, headers=self.headers)
        response_json = response.json()
        # print(response_json)
        activity_info = response_json['data']

        message = MessageClass()
        message.message_text = "Activities"

        for i in range(len(activity_info)):
            attachment = MessageAttachmentsClass()
            attachment.text = "Activity" + " " + str(i + 1)

            field1 = AttachmentFieldsClass()
            field1.title = "Activity Subject"
            field1.value = activity_info[i]['subject']
            attachment.attach_field(field1)

            field2 = AttachmentFieldsClass()
            field2.title = "Activity Type"
            field2.value = activity_info[i]['type']
            attachment.attach_field(field2)

            field3 = AttachmentFieldsClass()
            field3.title = "Due Date"
            field3.value = activity_info[i]['due_date']
            attachment.attach_field(field3)

            field4 = AttachmentFieldsClass()
            field4.title = "Contact Person"
            field4.value = "-" if activity_info[i]['person_name'] is None else activity_info[i]['person_name']
            attachment.attach_field(field4)

            field5 = AttachmentFieldsClass()
            field5.title = "Company"
            field5.value = "-" if activity_info[i]['org_name'] is None else activity_info[i]['org_name']
            attachment.attach_field(field5)

            field6 = AttachmentFieldsClass()
            field6.title = "Handled by"
            field6.value = activity_info[i]['owner_name']
            attachment.attach_field(field6)

            message.attach(attachment)
        return message.to_json()
