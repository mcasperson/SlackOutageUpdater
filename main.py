import logging
import argparse
import base64
from datetime import datetime
from slack_sdk import WebClient

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser(description='Find the unanswered posts in Slack.')
parser.add_argument('--slackApiToken',
                    dest='slack_api_token',
                    action='store',
                    help='The Slack API token',
                    required=True)
parser.add_argument('--slackChannelName',
                    dest='slack_channel_name',
                    action='store',
                    help='The Slack channel name',
                    required=True)
parser.add_argument('--octopusOutputVars',
                    dest='octopus_output_vars',
                    action='store_true',
                    help='The Slack channel name')
args = parser.parse_args()


def find_slack_channel(client, channel_name):
    channels = client.conversations_list()
    for channel in channels.data['channels']:
        if channel['name'] == channel_name:
            return channel['id']

    raise Exception("cannot find channel " + channel_name)


def get_messages(client, channel_id):
    result = client.conversations_history(channel=channel_id)
    return result


def get_unanswered_messages(client, channel_id, messages):
    links = []
    for message in messages.data["messages"]:
        age = (datetime.now() - datetime.fromtimestamp(float(message['ts']))).total_seconds()
        # Only get messages from the last day (with one hour overlap to catch any edge cases)
        if age < 60 * 60 * 25:
            # Subtypted messages tend to be things like users joining, so ignore those
            if "subtype" not in message:
                # The presence of thread_ts means this is a threaded conversation
                if "thread_ts" not in message:
                    links.append({
                        "link": client.chat_getPermalink(
                            channel=channel_id, message_ts=message["ts"]).data["permalink"],
                        "text": message["text"]})
    return links


def display_links(links):
    print("The following messages do not have any threaded replies.")
    for link in links:
        print(link["link"] + ": " + link["text"])


def find_messages_without_threads():
    client = WebClient(token=args.slack_api_token)
    channel_id = find_slack_channel(client, args.slack_channel_name)
    messages = get_messages(client, channel_id)
    links = get_unanswered_messages(client, channel_id, messages)
    display_links(links)
    if args.octopus_output_vars:
        print("##octopus[setVariable name='"
              + base64.b64encode("UnansweredMessageCount".encode('ascii')).decode("ascii")
              + "' value='" + base64.b64encode(str(len(links)).encode('ascii')).decode("ascii") + "']")
        print("##octopus[setVariable name='"
              + base64.b64encode("UnansweredMessages".encode('ascii')).decode("ascii")
              + "' value='" + base64.b64encode(str(len(links) != 0).encode('ascii')).decode("ascii") + "']")


find_messages_without_threads()
