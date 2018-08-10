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

    def scrape(self, carry_over):
        #nScrape Tweets from all users in the reporters.txt file tweeted in the last 6 seconds.
        to_post = []
        with open(REPORTERS) as f:
            for line in f:
                name = line.split(',')[0]
                id = int(line.split(',')[1])
                screen_name = line.split(',')[2].split('\n')[0]
                statuses = self.api.GetUserTimeline(id, count=5)
                for tweet in statuses:
                    age = time.time() - tweet.created_at_in_seconds
                    if not tweet.retweeted_status and tweet.in_reply_to_user_id == None and tweet.quoted_status == None and age < (6 + carry_over):
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

    def check_for_duplicates(self, number_of_posts):
        # Delete post(s) if someone already posted it (them).
        if number_of_posts == 0:
            return
        for my_submission in self.user.submissions.new(limit=number_of_posts):
            for submission in self.nba.new(limit=15):
                if int(submission.created_utc) < int(my_submission.created_utc) and submission.url == my_submission.url:
                    id = submission.url.split('/')[5]
                    with open(REPORTERS) as f:
                        for line in f:
                            parts = line.split(',')
                            if parts[2] == id:
                                fragment = ''.join(['[', parts[0], ']'])
                                if fragment in submission.title:
                                    my_submission.delete()
                                    with open('logs.txt', 'a') as f:
                                        f.write(''.join(['Deleted the following post because ', submission.author, ' posted first:\n', my_submission.title, '\nTheir post: ', submission.title, '\n']))

    def check_for_feedback(self, number_of_posts):
        # Delete post(s) if not received well. Serves as relevance test.
        if number_of_posts == 0:
            return
        for my_submission in self.user.submissions.new(limit=number_of_posts):
            if int(my_submission.score) < 0 and my_submission.title[0] == '[':
                my_submission.delete()
                with open('logs.txt', 'a') as f:
                    f.write(''.join(['Deleted the following post because it had a sub-zero score:\n', my_submission.title, '\n']))

if __name__ == '__main__':
    if len(sys.argv) != 4: # Specify usage
        print("Usage: python3 testing_praw.py reddit.txt twitter.txt reporters.txt")
        sys.exit(1)
    try:
        bot = RedditBot(sys.argv[1])
    except Exception:
        print("Reddit authentication failed. Check ", sys.argv[1])
        sys.exit(2)
    try:
        twitter_bot = TweetScraper(sys.argv[2])
    except Exception:
        print("Twitter authentication failed. Check ", sys.argv[2])
        sys.exit(3)
    try:
        with open(sys.argv[3]) as f:
            if sum(1 for line in f) == 0:
                print(sys.argv[3], " is empty.")
                sys.exit(4)
    except IOError:
        print ("Could not read ", sys.argv[3])
        sys.exit(5)
    REPORTERS = sys.argv[3]
    with open('logs.txt', 'w') as f:
        f.write('Logs:\n')
    delay = 0
    left_over = 0
    new_posts = 0
    check_time = None
    print('Running')
    while True: # Main loop
        init_time = time.time() # Begin stopwatch
        contents = twitter_bot.scrape(left_over)
        if contents != None:
            for i in range(0, len(contents), 2):
                bot.submit(contents[i], contents[i+1])
            check_time = time.time()
            new_posts += len(contents) / 2
        if check_time != None and time.time() - check_time > 300:
            # Only check for duplicates and relevance if no tweets have been posted in 5 mins so as to minimize hangups.
            bot.check_for_duplicates(new_posts)
            bot.check_for_feedback(new_posts)
            new_posts = 0
        delay = time.time() - init_time # Stop stopwatch
        try:
            time.sleep(5 - delay - left_over) # Account for delays by shortening sleep period.
            left_over = 0
        except ValueError:
            left_over = delay - 5
