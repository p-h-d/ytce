# coding=utf-8
'''
Created on 2018/05/04

@author: snakagawa
'''

import os.path
import httplib2
from oauth2client import tools, client
from oauth2client.file import Storage
    
import json
import time
import sys

import argparse

class Manager(object):
    
    MAX_LOADED_MESSAGE = 200
    DELETE_LOADED_MESSAGE = 100
    
    def __init__(self, path_config):
        
        
        # Load configuration file
        with open(path_config, "r") as f:
            di = json.load(f)
        
        live_channel_ids = di["live_channel_ids"]
        api_key_file = di["api_key_file"]
        credentials_file = di["credentials_file"]
        author_channel_ids = di["author_channel_ids"]
        log_file = di["log_file"]
        
        # 
        if os.path.exists(credentials_file):
            # already authorized
            store = Storage(credentials_file)
            credentials = store.get()
        else:
            # authorize
            scope = "https://www.googleapis.com/auth/youtube.readonly"
            flow = client.flow_from_clientsecrets(api_key_file, scope)
            flow.user_agent = "chatextractor"
            credentials = tools.run_flow(flow, Storage(credentials_file))

        http = credentials.authorize(httplib2.Http())
        
        lives = {}
        
        for key, channel_id in live_channel_ids.items():
            try:
                l = Live(channel_id, http)
            except ValueError:
                print("Failed to connect: {0}: {1}".format(key, channel_id))
            else:
                print("Connected: \"{0}\" by {1}".format(l.title, l.channeltitle))
                lives[key] = l
        
        self.lives = lives
        self.live_channel_ids = live_channel_ids
        self.author_channel_ids = author_channel_ids
        self.http = http
        self.displayed_message_ids = []
        self.log_file = log_file
    
    def log(self, string):
        '''
        Append to the log
        '''
        with open(self.log_file, "a", newline="") as f:
            f.write(string)
    
    def run(self):
        
        for live in self.lives.values():
            try:
                data = live.get_chat_data()
            except ValueError:
                pass
            else:
                for item in data["items"]:
                    try:
                        snippet = item["snippet"]
                        author_detail = item["authorDetails"]
                    
                        author_channel_id = snippet["authorChannelId"]
                        published_time = snippet["publishedAt"]
                    except KeyError:
                        continue

                    # define messsage id
                    message_id = author_channel_id + published_time 
                    
                    # if the author is not in the list, ignore. 
                    if self.author_channel_ids:
                        if author_channel_id not in self.author_channel_ids.values():
                            continue
                
                    # if the message is already loaded, ignore.
                    if message_id in self.displayed_message_ids:
                        continue
                    
                    # if the message is new,
                    # add the message id to the "already displayed" list. 
                    self.displayed_message_ids.append(message_id)
                    # print. 
                    # print(snippet["publishedAt"], "@", "\"" + live.title + "\"", author_detail["displayName"], snippet["displayMessage"])
                    
                    string = "\t".join([snippet["publishedAt"], 
                                        live.title, 
                                        author_detail["displayName"], 
                                        snippet["displayMessage"]]) + "\n"
                    try:
                        self.log(string)
                    except (IOError, OSError):
                        sys.stderr.write("Failed to write to {0}. \n".format(self.log_file))
                        sys.stderr.write(string)
        
        # flush some of the displayed message ids to prevent the list from expanding forever
        if len(self.displayed_message_ids) > self.MAX_LOADED_MESSAGE:
            self.displayed_message_ids = self.displayed_message_ids[self.DELETE_LOADED_MESSAGE:] 
        
    def start(self, pollsec=1.0):
        
        print("Started retrieving chat data...")
        
        while True:
            self.run()
            time.sleep(pollsec)

def get_data(http, url):
    res, data = http.request(url)
    data = json.loads(data.decode())
    
    return data

def get_live_data(channel_id, http):
    '''
    Get information of the live stream based on a channel id. 
    
    @param channel_id: channel id
    @param http: http2lib.Http() instance
    '''

    url = "https://www.googleapis.com/youtube/v3/search?part=snippet&channelId=" + channel_id + "&eventType=live&type=video"
    channel_data = get_data(http, url)
    
    try:
        video_id = channel_data["items"][0]["id"]["videoId"]
    except (KeyError, IndexError):
        return None
    
            
    url = "https://www.googleapis.com/youtube/v3/videos?part=liveStreamingDetails,snippet&id=" + video_id
    live_data = get_data(http, url)
    
    return live_data


class Live(object):
    
    def __init__(self, channel_id, http):
        '''
        Retrieves and stores the data related to the live in the specified channel. 
                
        @param channel_id: channel id of the owner of the live (string). 
        @param http: an http2lib.Http() instance to send requests.
        
        @ivar http: an http2lib.Http() instance to send requests.
        @ivar chat_id: live chat id of the live. 
        @ivar title: title of the live video. 
        '''
        
        li_data = get_live_data(channel_id, http)
        
        if not li_data:
            raise ValueError("Cannot get chat id")
        
        try:
            title = li_data["items"][0]["snippet"]["title"]
            channeltitle = li_data["items"][0]["snippet"]["channelTitle"]
            chat_id = li_data["items"][0]["liveStreamingDetails"]["activeLiveChatId"]
        except (KeyError, IndexError):
            raise ValueError("Cannot get chat id")
        
        self.http = http
        self.chat_id = chat_id
        self.title = title
        self.channeltitle = channeltitle
    
    def get_chat_data(self):
        '''
        Returns all available chat data. 
        
        @raise ValueError: 
        '''
        
        url = "https://www.googleapis.com/youtube/v3/liveChat/messages?part=snippet,authorDetails"
        url += "&liveChatId=" + self.chat_id
        
        try:
            data = get_data(self.http, url)
        except json.decoder.JSONDecodeError:
            raise ValueError("JSON decode error")
        else:
            return data


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description="Print chat comments in specified lives made by specified channels. ")
    parser.add_argument("config_file", metavar="config_file", nargs=1, action="store")
    
    args = parser.parse_args()
    
    m = Manager(args.config_file[0])
    
    if not m.lives:
        sys.stderr.write("No one's on live now. \n")
    else:
        m.start()