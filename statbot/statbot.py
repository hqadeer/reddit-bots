import sys
import praw
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

    def load_relevant_players(self, limit=5):
        '''Loads players mentioned in recent r/nba comments to database.

        limit (int) -- specifies how many comments to parse for player names
        '''
        names = [name[0] for name in self.league.get_all_player_names()]
        info = {*[word.lower() for post in self.sub.new(limit=limit) for word
                in post.title.split(' ')]}
        relevant = set()
        for name in names:
            temp = name.split(' ')
            try:
                if temp[0] in info and temp[1] in info:
                    relevant.add(name)
            except IndexError:
                continue
        self.league.load_players(relevant)

if __name__ == "__main__":

    bot = StatBot('reddit.txt')
