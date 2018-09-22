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
        self.stats = self.league.get_valid_stats()


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

    def parse_name(self, words):
        '''Parse a comment's body for a player name and returns it

        words (list) -- list of words from body of praw.Comment object
        '''

        for i, word in enumerate(words[:-1]):
            fullname = ' '.join(word, words[i+1])
            if fullname in self.names:
                return fullname

    def parse_stats(self, words):
        '''Parse a comment's body for stat queries and returns a list of
           stats requested.

        words (list) -- list of words from body of praw.Comment object
        '''

        # Find a word within the comment containing a stat.
        # Split that word along its forward slashes.
        stat_word = [word for word in words if any([stat in word for stat in
                     self.stats])][0].split('/')
        return [stat for stat in stat_word if stat.upper() in self.stats]

    def parse_seasons(self, words):
        ''' Parse a comment's body for the season range requested and return it

        words (list) -- list of words from body of praw.Comment object
        '''

        def check(word):
        ''' Checks if a word specifies a year range'''
            if '-' not in word or len(word) != 7:
                return False
            try:
                return (int(word[5:]) > int(word[2:4]) and (int(word[:2]) == 19
                        or int(word[:2]) == 20))
            except ValueError:
                return False

        return [word for word in words if check(word)][0]

    def output(self, text, comment):
        ''' Format results and post them as a reply to comment
        Return ID and URL of response.

        results (list of tuples) -- output returned from get_stats query
        comment -- praw.Comment object
        '''

    def log(self, comment):

    def process(self, comment):
        '''Takes a comment and posts a reply providing the queried stat(s)

        comment (praw.Comment object) -- comment containing trigger
        '''
        words = comment.body.split(' ')
        name = self.parse_name(words)
        player = self.league.get_player(name)
        stats = self.parse_stats(words)
        seasons = self.parse_seasons(words)
        if '-p' in words or '-playoffs' in words:
            results = [player.get_stats(stats, seasons, mode='playoffs')]
        elif '-b' in words or '-both' in words:
            results = [player.get_stats(stats, seasons, mode='playoffs'),
                       player.get_stats(stats, seasons)]
        else:
            results = [player.get_stats(stats, seasons)] # mode='season'
        descrip = "Stats for %s:" % name.title()
        header = '|'.join(['Season'] + [stat.upper() for stat in stats])
        line = '-|' * (len(stats) + 1)
        self.log(self.output(text, comment))

    def run(self):
        '''Search for comments in r/nba containing "!STAT" and respond to them.

        This functions as the main loop of the program.
        '''
        for comment in self.sub.stream.comments():
            if "!STAT" in comment.body:
                self.process(comment)

if __name__ == "__main__":

    bot = StatBot('reddit.txt')
    bot.run()
