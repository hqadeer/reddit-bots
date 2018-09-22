import sys
import praw
import sqlite3
from nba_scrape import NBA

class StatBot:
    '''Reddit bot to provide NBA stats upon request.

    Usage TBD
    '''

    def __init__(self, reddit_file):
        '''Create praw instance using reddit_file.

        reddit_file (.txt) -- file containing client id, client secret,
                              user agent, username, and password
        '''

        info = []
        with open(reddit_file) as f:
            for line in f:
                info.append(line.split("=")[1].split("\n")[0])
        self.reddit = praw.Reddit(client_id = info[0], client_secret = info[1],
                                  user_agent = info[2], username=info[3],
                                  password =info[4])
        self.sub = self.reddit.subreddit('nba')
        self.league = NBA()
        self.names = [name[0] for name in self.league.get_all_player_names()]

    def load_relevant_players(self, limit=5):
        '''Loads players mentioned in recent r/nba comments to database.

        limit (int) -- specifies how many comments to parse for player names
        '''

        info = {*[word.lower() for post in self.sub.new(limit=limit) for word
                in post.title.split(' ')]}
        relevant = set()
        for name in self.names:
            temp = name.split(' ')
            try:
                if temp[0] in info and temp[1] in info:
                    relevant.add(name)
            except IndexError:
                continue
        return relevant
        self.league.load_players(relevant)

    def get_name(self, comment):
        '''Scrape a comment's body for a player name

        comment (string) -- body of praw.Comment object
        '''
        
        words = comment.body.split(' ')

        for i, word in enumerate(words[:-1]):
            fullname = ' '.join(word, words[i+1])
            if fullname in self.names:
                return fullname

    def process(self, comment):
        '''Takes a comment and posts a reply providing the queried stat(s)

        comment (praw.Comment object) -- comment containing trigger
        '''
        name = self.get_name(comment.body)






    def find_comments(self):
        '''Search for comments in r/nba containing "!STAT"

        This functions as the main loop of the program.
        '''

        for comment in self.sub.stream.comments():
            if "!STAT" in comment.body:
                self.process(comment)

if __name__ == "__main__":

    bot = StatBot('reddit.txt')
