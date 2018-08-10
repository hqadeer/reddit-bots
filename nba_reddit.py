import praw
import twitter
import sys
import time

class TweetScraper():
    def __init__(self, twitter_file):
        # Create Twitter instance using info file containing login and API credentials
        info = []
        with open(twitter_file) as f:
            for line in f:
                info.append(line.split("=")[1].split("\n")[0])
        self.api = twitter.Api(consumer_key = info[0], consumer_secret = info[1], access_token_key = info[2], access_token_secret = info[3])
        self.api.tweet_mode='extended'

    def scrape(self):
        #Scrape Tweets from all users in the reporters.txt file tweeted in the last 11 seconds.
        f = open('reporters.txt')
        to_post = []
        for line in f:
            name = line.split(',')[0]
            id = int(line.split(',')[1])
            screen_name = line.split(',')[2].split('\n')[0]
            statuses = self.api.GetUserTimeline(id, count=5)
            for tweet in statuses:
                age = time.time() - tweet.created_at_in_seconds
                if not tweet.retweeted_status and tweet.in_reply_to_user_id == None and tweet.quoted_status == None and age < (11):
                    text = tweet.full_text
                    rpost = text.split(' http')
                    to_post.append(''.join(['[', name, '] ', rpost[0]]))
                    to_post.append(''.join(['www.twitter.com/', screen_name, 'status/', str(tweet.id)]))
        if len(to_post) > 0:
            return to_post

class RedditBot:
    def __init__(self, reddit_file):
        # Create Reddit instance using info file
        info = []
        with open(reddit_file) as f:
            for line in f:
                info.append(line.split("=")[1].split("\n")[0])
        self.reddit = praw.Reddit(client_id = info[0], client_secret = info[1],
        user_agent = info[2], username=info[3], password =info[4])
        self.nba = self.reddit.subreddit('nba')
        self.user = self.reddit.redditor(info[3])

    def submit(self, title, web_url):
        #Submit post to reddit and print to standard output
        self.nba.submit(title, url=web_url)
        print(title)
        print(web_url)

    def __get_comments(self):
        #Deprecated method to play around with API
        timer = time.time() + 5
        count = 0
        a = ['lakers', 'Lakers', 'LAL', 'GSW', 'Warriors', 'warriors']
        comments = self.nba.stream.comments()
        for comment in comments:
            if time.time() < timer:
                if any(x in comment.body for x in a):
                    print (comment.body)
                count += 1
            else:
                print (count)
                break

    def check_for_duplicates(self):
        # Delete post(s) if someone already posted it (them).
        for my_submission in self.user.submissions.new(limit=3):
            for submission in self.nba.new(limit=15):
                if int(submission.created_utc) < int(my_submission.created_utc) and submission.url == my_submission.url:
                    id = submission.url.split('/')[5]
                    with open('reporters.txt') as f:
                        for line in f:
                            parts = line.split(',')
                            if parts[2] == id:
                                fragment = ''.join(['[', parts[0], ']'])
                                if fragment in submission.title:
                                    my_submission.delete()

    def check_for_relevance(self):
        # Delete post(s) if not received well. Serves as relevance test.
        for my_submission in self.user.submissions.new(limit = 10):
            if int(my_submission.score) < 0 and my_submission.title[0] == '[':
                my_submission.delete()




if __name__ == '__main__':
    if len(sys.argv) != 3: # Specify usage
        print("Usage: python3 testing_praw.py reddit.txt twitter.txt")
        sys.exit(1)
    bot = RedditBot(sys.argv[1])
    twitter_bot = TweetScraper(sys.argv[2])
    delay = 0
    check_time = None
    while True: # Main loop
        init_time = time.time() # Begin stopwatch
        contents = twitter_bot.scrape()
        if contents != None:
            for i in range(0, len(contents), 2):
                bot.submit(contents[i], contents[i+1])
            check_time = time.time()
        if check_time != None and time.time() - check_time > 120:
            # Only check for duplicates and relevance if no tweets have been posted in 5 mins so as to minimize hangups.
            bot.check_for_duplicates()
            bot.check_for_relevance()
        delay = time.time() - init_time # Stop stopwatch
        try:
            time.sleep(10 - delay) # Account for delays by shortening sleep period.
        except ValueError:
            time.sleep(0)
