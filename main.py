import logging
import argparse
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
        if "subtype" not in message:
            if "thread_ts" not in message:
                links.append(client.chat_getPermalink(channel=channel_id, message_ts=message["ts"]).data["permalink"])
    return links


client = WebClient(token=args.slack_api_token)
channel_id = find_slack_channel(client, args.slack_channel_name)
messages = get_messages(client, channel_id)
get_unanswered_messages(client, channel_id, messages)
