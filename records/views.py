""" This file contains all functions corresponding to their urls"""

import json
import uuid
import traceback
from django.http import HttpResponseRedirect, HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from yellowant import YellowAnt
from yellowant.messageformat import MessageClass, MessageAttachmentsClass, \
    MessageButtonsClass, AttachmentFieldsClass
from records.models import YellowUserToken, YellowAntRedirectState, \
    AppRedirectState, PipedriveUserToken
from records.commandcentre import CommandCentre


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
                                        ['user_application'],
                                        webhook_id=hash_str)
    state = str(uuid.uuid4())
    AppRedirectState.objects.create(user_integration=ut, state=state)
    PipedriveUserToken.objects.create(user_integration=ut, pipedrive_api_token="")

    # Redirecting to home page
    return HttpResponseRedirect("/")


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

            # # Appropriate function calls for corresponding webhook functions
            # if function_name == 'create_incident' and flag == 1:
            #     add_new_incident(request)
            # if function_name == 'add_user' and flag == 1:
            #     add_new_user(request)
            # # Returning message response
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
