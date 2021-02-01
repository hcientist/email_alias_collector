# from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from collections import defaultdict
# import sys
from httplib2 import Http
import re
import sys
import time
# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

aliases = defaultdict(list)


def main(domain="example.com"):
    # callback for the batch request (see below)
    def handle_message(request_id, response, exception):
        pattern = f"[^\"'<\s]+@{domain}"
        # print('\n\nhandle_message\n\n')
        if exception is not None:
            print(f'messages.get failed for message id {request_id}: {exception}')
        else:
            # print(response)
            try:
                to_addr = response['payload']['headers'][0]['value']
                # print(to_addr)
                matches = set(re.findall(pattern, to_addr))
                for match in matches:
                    # print(match)
                    aliases[match.upper()].append(response['id'])
            except KeyError as ke:
                print("keyerror", ke)
            # sys.exit(0)
            # aliases[response[]]
        # print(aliases)

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    http = Http()
    service = build('gmail', 'v1', credentials=creds)

    msg_list_params = {
        'userId': 'me',
        'q': 'to:@emjmays.com -(to:emily@emjmays.com)'
    }

    # messages.list API
    message_list_api = service.users().messages()
    # first request
    message_list_req = message_list_api.list(**msg_list_params)
    # print('message_list_req is not None', message_list_req is not None)
    while message_list_req is not None:
    # print('in while')
        gmail_msg_list = message_list_req.execute()

        # we build the batch request
        batch = service.new_batch_http_request(callback=handle_message)
        # gmail_message = gmail_msg_list['messages'][0]
        for gmail_message in gmail_msg_list['messages']:
            msg_get_params = {
                'userId': 'me',
                'id': gmail_message['id'],
                'format': 'metadata',
                'metadataHeaders': 'To'
            }
            batch.add(service.users().messages().get(**msg_get_params),
                      request_id=gmail_message['id'])

        batch.execute(http=http)
        time.sleep(10)

        # pagination handling
        message_list_req = message_list_api.list_next(message_list_req,
                                                      gmail_msg_list)
    time.sleep(60)
    with open("/Users/tgm/Downloads/aliases.txt", "wt") as f:
        for address in aliases.keys():
            # print(address, len(x[address]))
            f.write(f"{address}: {len(aliases[address])}\n")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("USAGE: python collector.py example.com")
        sys.exit(1)
    main(sys.argv[1])
