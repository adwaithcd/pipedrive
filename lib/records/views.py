""" This file contains all functions corresponding to their urls"""

import json
import uuid
import traceback
from django.http import HttpResponseRedirect, HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from yellowant import YellowAnt
from yellowant.messageformat import MessageClass, MessageAttachmentsClass, \
    MessageButtonsClass
from .models import YellowUserToken, YellowAntRedirectState, \
    AppRedirectState, PipedriveUserToken
from .commandcentre import CommandCentre


def redirectToYellowAntAuthenticationPage(request):

    """Initiate the creation of a new user integration on YA
       YA uses oauth2 as its authorization framework.
       This method requests for an oauth2 code from YA to start creating a
       new user integration for this application on YA.
    """
    # Generate a unique ID to identify the user when YA returns an oauth2 code
    user = User.objects.get(id=request.user.id)
    state = str(uuid.uuid4())

    # Save the relation between user and state so that we can identify the user
    # when YA returns the oauth2 code
    YellowAntRedirectState.objects.create(user=user.id, state=state)

    # Redirect the application user to the YA authentication page.
    # Note that we are passing state, this app's client id,
    # oauth response type as code, and the url to return the oauth2 code at.
    return HttpResponseRedirect("{}?state={}&client_id={}&response_type=code&redirect_url={}".format
                                (settings.YELLOWANT_OAUTH_URL, state, settings.YELLOWANT_CLIENT_ID,
                                 settings.YELLOWANT_REDIRECT_URL))


def yellowantRedirecturl(request):

    """ Receive the oauth2 code from YA to generate a new user integration
            This method calls utilizes the YA Python SDK to create a new user integration on YA.
            This method only provides the code for creating a new user integration on YA.
            Beyond that, you might need to authenticate the user on
            the actual application (whose APIs this application will be calling)
            and store a relation between these user auth details and the YA user integration.
    """
    # Oauth2 code from YA, passed as GET params in the url
    code = request.GET.get('code')

    # The unique string to identify the user for which we will create an integration
    state = request.GET.get("state")

    # Fetch user with help of state from database
    yellowant_redirect_state = YellowAntRedirectState.objects.get(state=state)
    user = yellowant_redirect_state.user

    # Initialize the YA SDK client with your application credentials
    y = YellowAnt(app_key=settings.YELLOWANT_CLIENT_ID,
                  app_secret=settings.YELLOWANT_CLIENT_SECRET, access_token=None,
                  redirect_uri=settings.YELLOWANT_REDIRECT_URL)

    # Getting the acccess token
    access_token_dict = y.get_access_token(code)
    access_token = access_token_dict["access_token"]

    # Getting YA user details
    yellowant_user = YellowAnt(access_token=access_token)
    profile = yellowant_user.get_user_profile()

    # Creating a new user integration for the application
    user_integration = yellowant_user.create_user_integration()
    hash_str = str(uuid.uuid4()).replace("-", "")[:25]
    ut = YellowUserToken.objects.create(user=user, yellowant_token=access_token,
                                        yellowant_id=profile['id'],
                                        yellowant_integration_invoke_name=user_integration \
                                        ["user_invoke_name"],
                                        yellowant_integration_id=user_integration\
                                        ['user_application'], webhook_id=hash_str)
    state = str(uuid.uuid4())
    AppRedirectState.objects.create(user_integration=ut, state=state)
    PipedriveUserToken.objects.create(user_integration=ut, pipedrive_api_token="")

    # Redirecting to home page
    return HttpResponseRedirect("/")


@csrf_exempt
def add_new_user(request, webhook_id):
    """
        Webhook function to notify user about newly added user
    """

    # Extracting necessary data
    data = request.body
    data_string = data.decode('utf-8')
    data_json = json.loads(data_string)

    ID = data_json["current"][0]['id']
    name = data_json["current"][0]['name']
    Default_currency = data_json["current"][0]['default_currency']
    Email = data_json["current"][0]['email']
    phone = "-" if data_json["current"][0]['phone'] is None else data_json["current"][0]['phone']

    # Fetching yellowant object
    yellow_obj = YellowUserToken.objects.get(webhook_id=webhook_id)
    access_token = yellow_obj.yellowant_token
    integration_id = yellow_obj.yellowant_integration_id
    service_application = str(integration_id)

    # Creating message object for webhook message
    webhook_message = MessageClass()
    webhook_message.message_text = "New user added."+"\n" + "The username : " + str(name)\
                                   + "\nThe Email ID:" + str(Email)
    attachment = MessageAttachmentsClass()
    attachment.title = "Get user details"

    button_get_users = MessageButtonsClass()
    button_get_users.name = "1"
    button_get_users.value = "1"
    button_get_users.text = "Get all users"
    button_get_users.command = {
        "service_application": service_application,
        "function_name": 'list_users',
        "data": {
            'data': "test",
        }
    }

    attachment.attach_button(button_get_users)
    webhook_message.attach(attachment)
    # print(integration_id)
    # userinfo = response['data']
    # phone = "-" if userinfo['phone'] is None else userinfo['phone']
    webhook_message.data = {
        "name": name,
        "ID": ID,
        "Email": Email,
        "Phone": phone,
        "Default currency": Default_currency
    }

    # Creating yellowant object
    yellowant_user_integration_object = YellowAnt(access_token=access_token)

    # Sending webhook message to user
    send_message = yellowant_user_integration_object.create_webhook_message(
        requester_application=integration_id,
        webhook_name="new_user", **webhook_message.get_dict())

    return HttpResponse("OK", status=200)


@csrf_exempt
def add_new_deal(request, webhook_id):
    """
        Webhook function to notify user about newly added deal
    """

    # Extracting necessary data
    data = request.body
    data_string = data.decode('utf-8')
    data_json = json.loads(data_string)

    title = data_json["current"]['title']
    handled_by = data_json["current"]['owner_name']
    name = data_json["current"]['person_name']
    currency = data_json["current"]['currency']
    company = data_json["current"]['org_name']
    value = data_json["current"]['value']
    deal_email = data_json["current"]['cc_email']

    # Fetching yellowant object
    yellow_obj = YellowUserToken.objects.get(webhook_id=webhook_id)
    access_token = yellow_obj.yellowant_token
    integration_id = yellow_obj.yellowant_integration_id
    service_application = str(integration_id)

    # Creating message object for webhook message
    webhook_message = MessageClass()
    webhook_message.message_text = "New deal created."+"\n" + "The deal name : " + str(title) + "\nThe deal value:" \
                                   + str(currency)+" "+str(value)
    attachment = MessageAttachmentsClass()

    button_get_deal = MessageButtonsClass()
    button_get_deal.name = "1"
    button_get_deal.value = "1"
    button_get_deal.text = "Get all deals"
    button_get_deal.command = {
        "service_application": service_application,
        "function_name": 'list_all_deals',
        "data": {
            'data': "test",
        }
    }

    attachment.attach_button(button_get_deal)
    webhook_message.attach(attachment)
    # print(integration_id)
    webhook_message.data = {
        "Handled by": handled_by,
        "Name": name,
        "Title": title,
        "Company": company,
        "Value": value,
        "Currency": currency,
        "Deal_email": deal_email
    }

    # Creating yellowant object
    yellowant_user_integration_object = YellowAnt(access_token=access_token)

    # Sending webhook message to user
    send_message = yellowant_user_integration_object.create_webhook_message(
        requester_application=integration_id,
        webhook_name="new_deal", **webhook_message.get_dict())
    return HttpResponse("OK", status=200)


@csrf_exempt
def add_new_activity(request, webhook_id):
    """
                Webhook function to notify user about newly added pipeline
        """

    data = request.body
    data_string = data.decode('utf-8')
    data_json = json.loads(data_string)

    title = data_json["current"]['deal_title']
    handled_by = data_json["current"]['owner_name']
    name = data_json["current"]['person_name']
    company = data_json["current"]['org_name']
    deal_email = data_json["current"]['deal_dropbox_bcc']
    activity_type = data_json["current"]['type']
    due_date = data_json["current"]['due_date']

    # Fetching yellowant object
    yellow_obj = YellowUserToken.objects.get(webhook_id=webhook_id)
    access_token = yellow_obj.yellowant_token
    integration_id = yellow_obj.yellowant_integration_id
    service_application = str(integration_id)

    # Creating message object for webhook message
    webhook_message = MessageClass()
    webhook_message.message_text = "New activity added."+"\n" + "The deal name : " + str(title) + "\nThe activity date:" \
                                   + str(due_date)
    attachment = MessageAttachmentsClass()

    button_get_activity = MessageButtonsClass()
    button_get_activity.name = "1"
    button_get_activity.value = "1"
    button_get_activity.text = "Get all activities"
    button_get_activity.command = {
        "service_application": service_application,
        "function_name": 'list_activities',
        "data": {
            'data': "test",
        }
    }

    attachment.attach_button(button_get_activity)
    webhook_message.attach(attachment)
    # print(integration_id)
    webhook_message.data = {
        "Handled by": handled_by,
        "Contact Person": name,
        "Due Date": due_date,
        "Deal Title": title,
        "Activity Type": activity_type,
        "Company": company,
        "Deal_email": deal_email
    }

    # Creating yellowant object
    yellowant_user_integration_object = YellowAnt(access_token=access_token)

    # Sending webhook message to user
    send_message = yellowant_user_integration_object.create_webhook_message(
        requester_application=integration_id,
        webhook_name="new_activity", **webhook_message.get_dict())
    return HttpResponse("OK", status=200)


@csrf_exempt
def add_new_pipeline(request, webhook_id):
    """
            Webhook function to notify user about newly added pipeline
    """

    data = request.body
    data_string = data.decode('utf-8')
    data_json = json.loads(data_string)

    name = data_json["current"]['name']
    add_time = data_json["current"]['add_time']
    url_tile = data_json["current"]['url_title']
    order = data_json["current"]['order_nr']

    # Fetching yellowant object
    yellow_obj = YellowUserToken.objects.get(webhook_id=webhook_id)
    access_token = yellow_obj.yellowant_token
    integration_id = yellow_obj.yellowant_integration_id
    service_application = str(integration_id)

    # Creating message object for webhook message
    webhook_message = MessageClass()
    webhook_message.message_text = "New pipeline created."+"\n" + "The pipeline name : " + str(name)
    attachment = MessageAttachmentsClass()

    button_get_pipeline = MessageButtonsClass()
    button_get_pipeline.name = "1"
    button_get_pipeline.value = "1"
    button_get_pipeline.text = "Get all pipelines"
    button_get_pipeline.command = {
        "service_application": service_application,
        "function_name": 'list_pipelines',
        "data": {
            'data': "test",
        }
    }

    attachment.attach_button(button_get_pipeline)
    webhook_message.attach(attachment)
    # print(integration_id)
    webhook_message.data = {
        "Add Time": add_time,
        "Url title": url_tile,
        "Name": name,
        "Order": order,
    }

    # Creating yellowant object
    yellowant_user_integration_object = YellowAnt(access_token=access_token)

    # Sending webhook message to user
    send_message = yellowant_user_integration_object.create_webhook_message(
        requester_application=integration_id,
        webhook_name="new_pipeline", **webhook_message.get_dict())
    return HttpResponse("OK", status=200)


@csrf_exempt
@require_POST
def webhook(request, hash_str=""):
    # print("Inside webhook")
    data = request.body
    data_string = data.decode('utf-8')
    data_json = json.loads(data_string)
    # print(data_json)
    # print(data_json["meta"])

    if(data_json["meta"]["object"]) == "pipeline":
        # print("in pipeline webhook")
        add_new_pipeline(request, hash_str)

    elif(data_json["meta"]["object"]) == "user":
        # print("in user webhook")
        add_new_user(request, hash_str)

    elif(data_json["meta"]["object"]) == "deal":
        # print("in deal webhook")
        add_new_deal(request, hash_str)

    elif(data_json["meta"]["object"]) == "activity":
        # print("in activity webhook")
        add_new_activity(request, hash_str)

    return HttpResponse("OK", status=200)


@csrf_exempt
def yellowantapi(request):
    """
        Receive user commands from YA
    """
    try:

        # Extracting the necessary data
        data = json.loads(request.POST['data'])
        args = data["args"]
        service_application = data["application"]
        verification_token = data['verification_token']
        # function_id = data['function']
        function_name = data['function_name']
        # print(data)

        # Verifying whether the request is actually from YA using verification token
        if verification_token == settings.YELLOWANT_VERIFICATION_TOKEN:

            # Processing command in some class Command and sending a Message Object
            # Add_user and create_incident have flags to identify the status of the operation
            # and send webhook only if the operation is successful
            message = CommandCentre(data["user"], service_application, function_name, args).parse()

            # Returning message response
            return HttpResponse(message)
        else:
            # Handling incorrect verification token
            error_message = {"message_text": "Incorrect Verification token"}
            return HttpResponse(json.dumps(error_message), content_type="application/json")
    except Exception as e:
        # Handling exception
        print(str(e))
        traceback.print_exc()
        return HttpResponse("Something went wrong")
