"""
Functions corresponding to URL patterns of web app

"""
import json
import requests
from django.http import HttpResponse
from django.shortcuts import render
from yellowant import YellowAnt
from records.models import YellowUserToken, PipedriveUserToken


def user_login(request):
    """Sample Login Page"""
    return render(request, "login.html")


def index(request, path):
    """
        Loads the homepage of the app.
        index function loads the home.html page
    """
    # print('test')

    context = {
        "user_integrations": []
    }
    # Check if user is authenticated otherwise redirect user to login page
    if request.user.is_authenticated:
        user_integrations = YellowUserToken.objects.filter(user=request.user.id)
        print(user_integrations)
        for user_integration in user_integrations:
            context["user_integrations"].append(user_integration)
        return render(request, "home.html", context)
    else:
        return HttpResponse("Please login!")


def userdetails(request):
    """
        userdetails function shows the vital integration details of the user
    """
    # print("in userdetails")
    user_integrations_list = []
    # Returns the integration id,user_invoke_name for an integration
    if request.user.is_authenticated:
        user_integrations = YellowUserToken.objects.filter(user=request.user.id)
        print(user_integrations)
        for user_integration in user_integrations:
            try:
                pdut = PipedriveUserToken.objects.get(user_integration=user_integration)
                print(pdut)
                user_integrations_list.append({"user_invoke_name": user_integration.\
                                              yellowant_integration_invoke_name,
                                               "id": user_integration.id, "app_authenticated": True,
                                               "is_valid": pdut.apikey_login_update_flag})
            except PipedriveUserToken.DoesNotExist:
                user_integrations_list.append({"user_invoke_name": user_integration.\
                                              yellowant_integration_invoke_name,
                                               "id": user_integration.id,
                                               "app_authenticated": False})
    return HttpResponse(json.dumps(user_integrations_list), content_type="application/json")


def user_detail_update_delete_view(request, id=None):
    """
        This function handles the updating, deleting and viewing user details
    """
    print("In user_detail_update_delete_view")
    print(id)
    user_integration_id = id
    if request.method == "GET":
        # return user data
        print("in get")
        pdut = PipedriveUserToken.objects.get(user_integration=user_integration_id)
        return HttpResponse(json.dumps({
            "is_valid": pdut.apikey_login_update_flag
        }))

    # elif request.method == "DELETE":
    #     # deletes the integration
    #     access_token_dict = YellowUserToken.objects.get(id=id)
    #     access_token = access_token_dict.yellowant_token
    #     print(access_token)
    #     user_integration_id = access_token_dict.yellowant_integration_id
    #     print(user_integration_id)
    #     url = "https://api.yellowant.com/api/user/integration/%s"%(user_integration_id)
    #     yellowant_user = YellowAnt(access_token=access_token)
    #     print(yellowant_user)
    #     yellowant_user.delete_user_integration(id=user_integration_id)
    #     response_json = YellowUserToken.objects.get(yellowant_token=access_token).delete()
    #     print(response_json)
    #     return HttpResponse("successResponse", status=204)
    elif request.method == "PUT":
        # adds a new integration
        data = json.loads(request.body.decode("utf-8"))
        print(data)
        api_token = data['pipedrive_api_token']
        user_integration = data['user_integration']
        headers = {
            'Content-Type': 'application/json',
        }

        url = 'https://api.pipedrive.com/v1/users?api_token=' + api_token
        response = requests.get(url, headers=headers)
        # response_json = response.json()
        # data = response_json['users'][0]
        # response.status_code = 401
        # for i in range(len(data)):
        #     if data[i]['username'] == user_id:
        #         response.status_code = 200

        if response.status_code == 200:
            print("Valid")
            api_new = PipedriveUserToken.objects.get(user_integration_id=user_integration)
            api_new.pipedrive_api_token = api_token
            api_new.apikey_login_update_flag = True
            api_new.save()
            # print(api_new.victorops_api_id)
            # print(api_new.victorops_api_key)
            return HttpResponse("Submitted", status=200)
        else:
            print("Invalid")
            return HttpResponse("Invalid Credentials", status=401)
