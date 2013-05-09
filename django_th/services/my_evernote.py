# -*- coding: utf-8 -*-

from .services import ServicesMgr
from evernote.api.client import EvernoteClient
import evernote.edam.type.ttypes as Types
from django.conf import settings
from django.core.urlresolvers import reverse
from ..models import UserService
from ..models import ServicesActivated
import codecs

"""
    handle process with evernote
    put the following in settings.py

    TH_EVERNOTE = {
        'sandbox': True,
        'consumer_key': 'abcdefghijklmnopqrstuvwxyz',
        'consumer_secret': 'abcdefghijklmnopqrstuvwxyz',
    }
    sanbox set to True to make your test and False for production purpose
"""


class ServiceEvernote(ServicesMgr):

    def get_title(self):
        pass

    def get_body(self):
        pass

    def process_data(self, token, title, content):
        if token:
            client = EvernoteClient(
                token=token, sandbox=settings.TH_EVERNOTE['sandbox'])
            user_store = client.get_user_store()
            note_store = client.get_note_store()
            notebooks = note_store.listNotebooks()
            note = Types.Note()
            note.title = title.encode('utf-8')
            note.content = '<?xml version="1.0" encoding="UTF-8"?>'
            note.content += '<!DOCTYPE en-note SYSTEM ' \
                '"http://xml.evernote.com/pub/enml2.dtd">'
            note.content += '<en-note>'
            note.content += content.encode('utf-8')
            note.content += '</en-note>'
            created_note = note_store.createNote(note)

    def get_evernote_client(self, token=None):
        if token:
            return EvernoteClient(
                token=token,
                sandbox=settings.TH_EVERNOTE['sandbox'])
        else:
            return EvernoteClient(
                consumer_key=settings.TH_EVERNOTE['consumer_key'],
                consumer_secret=settings.TH_EVERNOTE['consumer_secret'],
                sandbox=settings.TH_EVERNOTE['sandbox'])

    def auth(self, request):
        """
            let's auth the user to the Service
        """
        client = self.get_evernote_client()
        callbackUrl = 'http://%s%s' % (
            request.get_host(), reverse('evernote_callback'))
        request_token = client.get_request_token(callbackUrl)

        # Save the request token information for later
        request.session['oauth_token'] = request_token['oauth_token']
        request.session['oauth_token_secret'] =\
            request_token['oauth_token_secret']

        # Redirect the user to the Evernote authorization URL
        # return the URL string which will be used by redirect()
        # from the calling func
        return client.get_authorize_url(request_token)

    def callback(self, request):
        """
            Called from the Service when the user accept to activate it
        """
        try:
            client = self.get_evernote_client()
            # finally we save the user auth token
            # As we already stored the object ServicesActivated
            # from the UserServiceCreateView now we update the same
            # object to the database so :
            # 1) we get the previous objet
            us = UserService.objects.get(
                user=request.user,
                name=ServicesActivated.objects.get(name='evernote'))
            # 2) then get the token
            us.token = client.get_access_token(
                request.session['oauth_token'],
                request.session['oauth_token_secret'],
                request.GET.get('oauth_verifier', '')
            )
            # 3) and save everything
            us.save()
        except KeyError:
            return '/'

        # note_store = client.get_note_store()
        # notebooks = note_store.listNotebooks()

        return 'evernote/callback.html'