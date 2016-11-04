from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView

from .models import Token, SocialGroups

from urllib.parse import parse_qs
import webbrowser
from datetime import datetime, timedelta
from django.utils import timezone
import vk
from twython import Twython
import requests

# id of vk.com application
APP_ID = 5587936

TWITTER_CONSUMER_KEY = 'elHaapMtQZ9ZDvkkYmkUOTEPA'
TWITTER_CONSUMER_SECRET = 'HpU3TxJ9qlXCIhRwqq0xGfBoHUiDxXt5W2j96yvJNFUFzTsKCW'
TWITTER_ACCESS_TOKEN = '2632236968-mkKBOxzhE29xXoq5FmVXruDBYA64QvDeCffLIaf'
TWITTER_ACCESS_SECRET = 'wrCI6WGSW6t0hjOl9ttKk1whi9nASheorlnXUwWo0JnDa'

FACEBOOK_KEY = '1753362084926312'
FACEBOOK_SECRET = '70ad1c034a3d339593ff145a451105b8'

def get_social_group(source, group_name):
    try:
        return SocialGroups.objects.get(source=source,group_name=group_name).group_id
    except:
        return False

def get_saved_auth_params():
    access_token = None
    user_id = None
    try:
        token = Token.objects.all()
        access_token = token[0].access_token
        user_id = token[0].user_id
    except:
        pass
    return access_token, user_id


def save_auth_params(access_token, expires_in, user_id, source):
    expires = timezone.now() + timedelta(seconds=int(expires_in))
    Token.objects.create(access_token=access_token, expires=expires, user_id=user_id, source=source)

#
# def get_auth_params():
#     auth_url = ("https://oauth.vk.com/authorize?client_id={app_id}"
#                 "&scope=wall,messages&redirect_uri=http://oauth.vk.com/blank.html"
#                 "&display=page&response_type=token".format(app_id=APP_ID))
#     webbrowser.open_new_tab(auth_url)
#     redirected_url = input("Paste here url you were redirected:\n")
#     aup = parse_qs(redirected_url)
#     aup['access_token'] = aup.pop(
#         'https://oauth.vk.com/blank.html#access_token')
#     save_auth_params(aup['access_token'][0], aup['expires_in'][0],
#                      aup['user_id'][0])
#     return aup['access_token'][0], aup['user_id'][0]


def send_message(api, user_id, message, **kwargs):
    data_dict = {
        'user_id': user_id,
        'message': message,
    }
    data_dict.update(**kwargs)
    return api.messages.send(**data_dict)

def group_wall_post(group_id, message, access_token):
    api = get_api(access_token)
    return api.wall.post(owner_id=-group_id, message=message)

def get_api(access_token):
    session = vk.Session(access_token=access_token)
    return vk.API(session)


class VkView(TemplateView):
    template_name = 'a.html'

    def get(self, request,  *args, **kwargs):
        access_token, _ = get_saved_auth_params()
        if not access_token or not _:
            auth_url = ("https://oauth.vk.com/authorize?client_id={app_id}"
                        "&scope=wall,messages&redirect_uri=http://oauth.vk.com/blank.html"
                        "&display=page&response_type=token".format(app_id=APP_ID))
            webbrowser.open_new_tab(auth_url)
        else:
            group_id = get_social_group('vk', 'socio')
            group_wall_post(group_id, 'hello world', access_token)

        return render(request, 'a.html')

    def post(self, request,  *args, **kwargs):
        redirected_url=request.POST.get('a', '')
        aup = parse_qs(redirected_url)
        aup['access_token'] = aup.pop(
            'https://oauth.vk.com/blank.html#access_token')
        save_auth_params(aup['access_token'][0], aup['expires_in'][0],
                         aup['user_id'][0], 'vk')
        access_token = aup['access_token'][0]

        group_id = get_social_group('vk', 'socio')
        group_wall_post(group_id,'hello world', access_token)

        return render(request, 'a.html')


class TwitterView(View):
    def get(self, request, *args, **kwargs):
        twitter = Twython(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
        auth = twitter.get_authentication_tokens('http://127.0.0.1:8000/twitter/callback')
        request.session['twitter_oauth_token'] = auth['oauth_token']
        request.session['twitter_oauth_token_secret'] =  auth['oauth_token_secret']

        return HttpResponseRedirect(auth['auth_url'])


class TwitterCallbackView(View):
    def get(self, request, *args, **kwargs):
        oauth_verifier = request.GET.get('oauth_verifier', '')

        OAUTH_TOKEN=request.session['twitter_oauth_token']
        OAUTH_TOKEN_SECRET=request.session['twitter_oauth_token_secret']
        twitter = Twython(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET,
                          OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

        final_step = twitter.get_authorized_tokens(oauth_verifier)

        OAUTH_TOKEN = final_step['oauth_token']
        OAUTH_TOKEN_SECRET = final_step['oauth_token_secret']

        twitter = Twython(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET,
                          OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

        twitter.update_status(status='See how easy using Twython is!')

        return HttpResponse('ok')


class FacebookView(View):
    def get(self, request, *args, **kwargs):
        url = 'https://www.facebook.com/dialog/oauth?client_id={}&redirect_uri={}&scope=manage_pages%2Cpublish_stream' \
              '&state={}'.format(FACEBOOK_KEY, 'http://127.0.0.1:8000/facebook/callback', '123')
        # webbrowser.open_new_tab(url)
        return HttpResponseRedirect(url)

class FacebookCallbackView(View):
    def get(self, request, *args, **kwargs):
        r = requests.get('https://graph.facebook.com/oauth/access_token?client_id={}'
                         '&client_secret={}&code={}'.format(FACEBOOK_KEY, FACEBOOK_SECRET, request.GET.get('code')))

        token = r.text
        return HttpResponse(token)