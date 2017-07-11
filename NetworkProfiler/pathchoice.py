class PathChoice():

    CHOICE_SHORTEST = "Shortest Path Length"
    CHOICE_FIELD_NOT_EMPTY = "Field not empty"
    CHOICE_FIELD_VALUE = "Field has value"
    CHOICE_FIELD_NOT_VALUE = "Field does not have value"

    def __init__(self, choice=None, fieldname=None, fieldval=None):

        if choice is None:
            choice = PathChoice.CHOICE_SHORTEST

        self.fieldname = fieldname
        self.fieldval = fieldval
        self.choice = choice

        if fieldname is None and choice == PathChoice.CHOICE_FIELD_VALUE or choice == PathChoice.CHOICE_FIELD_NOT_EMPTY:
            raise Exception("ERROR: If you want to use a field option you need to specify a field")

        if fieldval is None and choice == PathChoice.CHOICE_FIELD_VALUE:
            raise Exception("ERROR: If you your path choice involves a field value you must provide one")

    def choose(self, features, node):
        """
        Choose one of the paths based on a set of rules
        :param features:
        :param node:
        :return:
        """

        if self.choice == PathChoice.CHOICE_FIELD_VALUE:
            features = filter(lambda x: x['name'] == self.fieldname and x['value'] == self.fieldval, features)

        elif self.choice == PathChoice.CHOICE_FIELD_NOT_VALUE:
            features = filter(lambda x: x['name'] == self.fieldname, features)

        elif self.choice == PathChoice.CHOICE_FIELD_NOT_EMPTY:
            features = filter(lambda x: x, features)

        # If the choice still hasn;t been made then use the shortest path
        if len(features) > 1:
            # Do a length lookup on remaining features and return the shortest one
            return sorted(features, key=lambda k: k['name'] )[0]
        else:
            # Just return the only choice
            return features[0]

    def _hasField(self):
        print

    def _valueMatch(self, fieldname, fieldvalue):
        print "thing"