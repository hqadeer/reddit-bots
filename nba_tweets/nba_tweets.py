import praw
import twitter
import sys
import time
import traceback

class TweetScraper:


    def __init__(self, twitter_file):

        # Create Twitter instance using twitter file.
        info = []
        with open(twitter_file) as f:
            for line in f:
                info.append(line.split('=')[1].split('\n')[0])
        self.api = twitter.Api(consumer_key = info[0], consumer_secret =
            info[1], access_token_key = info[2], access_token_secret = info[3])
        self.api.tweet_mode='extended'

    def scrape(self, carry_over):

        # Scrape recent tweets from all users in the reporters text file.
        to_post = []
        with open(REPORTERS) as f:
            for line in f:
                name = line.split(',')[0]
                id = int(line.split(',')[1])
                screen_name = line.split(',')[2].split('\n')[0]
                try:
                    statuses = self.api.GetUserTimeline(id, count=1)
                except ConnectionError:
                    message = "A connection error occurred."
                    with open('logs.txt', 'a') as f:
                        f.write(message)
                    print(message)
                    time.sleep(2)
                except Exception as exc:
                    message = "".join(["An error occurred in obtaining the",
                        " Twitter timeline for ", name, ":\nType is ",
                        exc.__class__.__name__, '\n\n'])
                    with open('logs.txt', 'a') as f:
                        f.write(message)
                    print(message)
                    traceback.print_exc()
                    return
                for tweet in statuses:
                    age = time.time() - tweet.created_at_in_seconds
                    if (not tweet.retweeted_status and
                            tweet.in_reply_to_user_id == None and
                            tweet.quoted_status == None and
                            age < (2.75 + carry_over)):
                        text = tweet.full_text
                        rpost = text.split(" http")
                        to_post.append("".join(['[', name, '] ', rpost[0]]))
                        to_post.append("".join(["www.twitter.com/", screen_name,
                            "/status/", str(tweet.id)]))
        if len(to_post) > 0:
            return to_post

class RedditBot:


    def __init__(self, reddit_file):

        # Create Reddit instance using info file.
        info = []
        with open(reddit_file) as f:
            for line in f:
                info.append(line.split("=")[1].split("\n")[0])
        self.reddit = praw.Reddit(client_id = info[0], client_secret = info[1],
        user_agent = info[2], username=info[3], password =info[4])
        self.nba = self.reddit.subreddit('nba')
        self.user = self.reddit.redditor(info[3])

    def submit(self, title, web_url):

        # Submit post to Reddit; print to logs file and standard output.
        self.nba.submit(title, url=web_url)
        message = ''.join(["Posted to r/nba:\nTitle: ", title, "\nURL: ",
            web_url, '\n\n'])
        with open('logs.txt', 'a') as f:
            f.write(message)
        print(message)

    def __get_comments(self):

        # Deprecated method to play around with API
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

        # Deletes a post if someone else posted it first and got more karma.
        if number_of_posts == 0:
            return
        for my_submission in self.user.submissions.new(limit=number_of_posts):
            for submission in self.nba.new(limit=10):
                if (int(submission.created_utc) < int(my_submission.created_utc)
                        and submission.url == my_submission.url and
                        submission.score > my_submission.score):
                    id = submission.url.split('/')[5]
                    with open(REPORTERS) as f:
                        for line in f:
                            parts = line.split(',')
                            if parts[2] == id:
                                fragment = ''.join(['[', parts[0], ']'])
                                if fragment in submission.title:
                                    my_submission.delete()
                                    message = (''.join(["Deleted the following",
                                    " post because ", submission.author,
                                    " posted first:\n", my_submission.title,
                                    "\nTheir post: ", submission.title, '\n\n']))
                                    with open('logs.txt', 'a') as f:
                                        f.write(message)
                                    print(message)

    def check_for_feedback(self, number_of_posts):

        # Delete post if score <= 0 five minutes after it was posted.
        if number_of_posts == 0:
            return
        for my_submission in self.user.submissions.new(limit=number_of_posts):
            if int(my_submission.score) <= 0 and my_submission.title[0] == '[':
                my_submission.delete()
                message = (''.join(["Deleted the following post because it had",
                " a sub-zero score:\n", my_submission.title, '\n\n']))
                with open('logs.txt', 'a') as f:
                    f.write(message)
                print(message)

if __name__ == '__main__':

    # Exception handling
    if len(sys.argv) != 4:
        print("Usage: python3 testing_praw.py <reddit file> <twitter file>",
            "<reporter file>")
        sys.exit(1)
    try:
        bot = RedditBot(sys.argv[1])
    except FileNotFoundError:
        print("Could not find", sys.argv[1])
        sys.exit(2)
    except Exception as exc:
        print("Reddit authentication failed. Check", sys.argv[1])
        print("Type of exception:", exc.__class__.__name__)
        traceback.print_exc()
        sys.exit(2)
    try:
        twitter_bot = TweetScraper(sys.argv[2])
    except FileNotFoundError:
        print("Could not find", sys.argv[2])
        sys.exit(3)
    except Exception as exc:
        print("Twitter authentication failed. Check", sys.argv[2])
        print("Type of exception:", exc.__class__.__name__)
        traceback.print_exc()
        sys.exit(3)
    try:
        with open(sys.argv[3]) as f:
            if sum(1 for line in f) == 0:
                print(sys.argv[3], "is empty.")
                sys.exit(4)
    except IOError:
        print ("Could not read", sys.argv[3])
        sys.exit(5)

    # Declaring loop variables and setting up logs text file.
    REPORTERS = sys.argv[3]
    with open('logs.txt', 'w') as f:
        f.write("Logs:\n\n")
    delay = 0
    left_over = 0
    new_posts = 0
    check_time = None
    print("Running")

    # Main loop
    while True:
        init_time = time.time() # Begin stopwatch
        contents = twitter_bot.scrape(left_over)
        if contents != None:
            for i in range(0, len(contents), 2):
                bot.submit(contents[i], contents[i+1])
            check_time = time.time()
            new_posts += len(contents) / 2
        if new_posts != 0 and time.time() - check_time > 300:
            # Check for feedback and duplicates if no tweets posted in 5 mins.
            bot.check_for_duplicates(new_posts)
            bot.check_for_feedback(new_posts)
            new_posts = 0
        delay = time.time() - init_time # Stop stopwatch
        try:
            time.sleep(2 - delay)
            left_over = 0
        except ValueError:
            left_over = delay - 2
