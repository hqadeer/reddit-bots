import praw
import sqlite3
import time
import traceback
from nba_scrape import NBA

class StatBot:
    '''Reddit bot to provide NBA stats upon request.

    Usage: !STAT player_name stat1/stat2/.../statn [season_range] [-flag]

    Season Range (optional parameter):
    Returns all seasons (including career averages) by default.
    Ranges must be in the format YYYY-YY (i.e. 2017-18 or 2014-18). "career" is
    also accepted; this returns overall career stats.

    Flags (optional parameter):
    -p or -playoffs for playoff stats
    -r or -season for regular season stats (default option)
    -b or -both for both

    Example: !STAT Lebron James pts/reb/ast/ts% 2014-18 -b
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
        self.sub = self.reddit.subreddit('experimental120394')
        self.league = NBA()
        self.names = [name[0] for name in self.league.get_all_player_names()]
        self.stats = self.league.get_valid_stats()
        self.database = 'logs.db'
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        cursor.execute('''create table if not exists logs(comment TEXT,
                       url TEXT, response TEXT)''')
        db.close()


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
        print('Loading %d players:' % len(relevant), relevant)
        self.league.load_players(relevant)

    def parse_name(self, words):
        '''Parse a comment's body for a player name and returns it

        words (list) -- list of words from body of praw.Comment object
        '''

        for i, word in enumerate(words[:-1]):
            fullname = word + ' ' + words[i+1]
            if fullname.lower() in self.names:
                return fullname.lower()

    def parse_stats(self, words):
        '''Parse a comment's body for stat queries and returns a list of
           stats requested.

        words (list) -- list of words from body of praw.Comment object
        '''

        # Find a word within the comment containing a stat.
        # Split that word along its forward slashes.
        try:
            stat_word = [word for word in words if any([stat in word.upper() for
                         stat in self.stats])][0].split('/')
        except IndexError:
            return
        return [stat.upper() for stat in stat_word if stat.upper() in
                self.stats]

    def parse_seasons(self, words):
        ''' Parse a comment's body for the season range requested and return it

        words (list) -- list of words from body of praw.Comment object
        '''

        def check(word):
            ''' Checks if a word specifies a year range'''
            if 'career' in word.lower():
                return True
            if '-' not in word or len(word) != 7:
                return False
            try:
                return (int(word[5:]) > int(word[2:4]) and (int(word[:2]) == 19
                        or int(word[:2]) == 20))
            except ValueError:
                return False
        try:
            return [word for word in words if check(word)][0]
        except IndexError:
            return

    def log(self, comment, response):
        '''Logs comment body, comment url, and response to database.'''

        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        try:
            cursor.execute('''insert into logs (comment, url, response)
                           values (?, ?, ?)''', (comment.body,
                           comment.permalink, response))
            db.commit()
        finally:
            db.close()
        return response

    def process(self, comment):
        '''Takes a comment and posts a reply providing the queried stat(s)

        comment (praw.Comment object) -- comment containing trigger
        '''
        words = comment.body.replace('\n', '').split(' ')
        name = self.parse_name(words)
        stats = self.parse_stats(words)
        year_range = self.parse_seasons(words)
        if name is None or not stats:
            print("Aborting because either name or stat was not found.")
            return
        if year_range == []:
            year_range = None
        player = self.league.get_player(name)
        if '-p' in words or '-P' in words or '-playoffs' in words:
            p_results = player.get_stats(stats, year_range, mode='playoffs')
            r_results = []
        elif '-b' in words or '-B' in words or '-both' in words:
            p_results = player.get_stats(stats, year_range, mode='playoffs')
            r_results = player.get_stats(stats, year_range)
        else:
            r_results = player.get_stats(stats, year_range) # mode='season'
            p_results = []
        if year_range is None:
            year_range = 'All Seasons'
        descrip = "Stats for %s (%s):\n" % (name.title(), year_range)
        header = '|'.join(['Season'] + [stat.upper() for stat in stats])
        line = '-|' * (len(stats) + 1)
        footer = "\n^This ^comment ^was ^generated ^by ^a ^bot."
        if r_results:
            r_data = [(pair[0],) + pair[1] for pair in r_results.items()]
            string_r = (['\n**Regular Season:**\n', header, line] +
                       ['|'.join([str(element) for element in tup]) for tup
                        in r_data])
        else:
            string_r = []
        if p_results:
            p_data = [(pair[0],) + pair[1] for pair in p_results.items()]
            string_p = (['\n**Playoffs:**\n', header, line] +
                        ['|'.join([str(element) for element in tup]) for tup
                        in p_data])
        else:
            string_p = []
        text = '\n'.join([descrip] + string_p + string_r + [footer])
        self.log(comment, text)
        comment.reply(text)

    def run(self):
        '''Search for comments in r/nba containing "!STAT" and respond to them.

        This functions as the main loop of the program.
        '''
        start_time = time.time()
        for comment in self.sub.stream.comments():
            if "!STAT" in comment.body and comment.created_utc >= start_time:
                print(comment.body)
                try:
                    self.process(comment)
                except Exception as exc:
                    traceback.print_exc()
                continue

class _Comment():
    '''Placeholder class for testing purposes'''
    def __init__(self, content):
        self.body = content
        self.permalink = 'blank'
        self.created_utc = 'blank'
    def reply(self, x):
        print('replying:', x)

if __name__ == "__main__":

    bot = StatBot('reddit.txt') # File containing login and API credentials.
