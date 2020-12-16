class Tweet(object):
    def __init__(self, content, polarity):
        self.content = content
        self.polarity = polarity

    def __str__(self):
        return "{} == {}".format(self.content, self.polarity)
