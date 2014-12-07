__author__ = 'Amish'

import os
import sys
import codecs
import re
import nltk
import unittest
import math
import matplotlib.pyplot as pyplot
import json

# Example using AFINN Data and the "SSAP"
# http://finnaarupnielsen.wordpress.com/2011/06/20/simplest-sentiment-analysis-in-python-with-af/
# Note that both self.word_valences and self.word_valences_lambda are equivalent
# I kept both for academic purposes (also, I didn't like the "simplified" version, so it's split
# over 3 lines

class AFINNData:
    def __init__(self):
        dirname = 'AFINN'
        filename = 'AFINN-111.txt'
        with codecs.open(os.path.join('..', dirname, filename), 'r', encoding='utf8') as f:
            lines = re.split(r'\n', f.read())
            self.word_valences = {}
            for line in lines:
                items = re.split(r'\t', line)
                if len(items) != 2:
                    # Invariant
                    raise NameError("The line has more than 2 items!")
                self.word_valences[items[0]] = int(items[1])

            # Example using lambdas
            self.key_val = [re.split(r'\t', w.strip()) for w in lines]

            # note that the Python 2.* way for lambdas is different than in 3.*
            # hence we had to change the code a little here
            self.my_map = map(lambda ws: (ws[0], int(ws[1])), self.key_val)
            self.word_valences_lambda = dict(self.my_map)

    def print_result(self, sent, filename=None):
        if filename == None:
            text = sent
        else:
            text = filename
        print("%6.2f %s" % (self.get_sentiment_for_sentence(sent), text))

    def get_valence_details(self, sent, store_not_found=False):
        result = dict()
        result['pos'] = []
        result['neg'] = []
        result['not_found'] = []
        words = list(filter(None, re.split(r"\W+", sent.lower())))

        for word in words:
            if word in self.word_valences:
                score = self.word_valences.get(word)
                if score > 0:
                    result['pos'].append([word, score])
                else:
                    result['neg'].append([word, score])
            else:
                if store_not_found:
                    result['not_found'].append(word)

        result['pos_total'] = sum([w[1] for w in result['pos']])
        result['neg_total'] = sum([w[1] for w in result['neg']])
        result['absolute_total'] = result['pos_total'] - result['neg_total']
        return result

    def get_sentiment_for_sentence(self, sent):
        """
        Returns a float for sentiment strength based on input text
        This is gratuitiously taken from the AFINN blog post
        """
        words = list(filter(None, re.split(r"\W+", sent.lower())))

        # this way is pretty stupid I think, sticking with list comprehension:
        #sentiments = map(lambda word: self.word_valences.get(word, 0), words)

        sentiments = [self.word_valences.get(w, 0) for w in words]

        if sentiments:
            sentiment = float(sum(sentiments)) / math.sqrt(len(sentiments))
        else:
            sentiment = 0
        return sentiment

class AFINN_tests(unittest.TestCase):
    def setUp(self):
        self.cut = AFINNData()

    def test_get_valence_for_hate_is_three(self):
        self.assertEqual(self.cut.word_valences['hate'], -3)

    def test_key_val(self):
        self.assertEqual(len(self.cut.key_val[0]), 2)

    def test_get_valence_lambda_for_hate_is_three(self):
        self.assertEqual(self.cut.word_valences_lambda['hate'], -3)

    def test_both_dicts_are_equal(self):
        self.assertEqual(len(self.cut.word_valences), len(self.cut.word_valences_lambda))
        for key in self.cut.word_valences:
            self.assertEqual(self.cut.word_valences[key], self.cut.word_valences_lambda[key])

    # Note that we use should use get(word, 0), since words not in the lexicon have 0 valence
    # Should we try to get a list of words which are not included? Maybe as a preprocessing?
    # YES
    def test_get_non_existent_word(self):
        with self.assertRaises(KeyError):
            self.cut.word_valences['rickyy']

    def test_special_chars_are_byebye(self):
        self.assertEqual(self.cut.get_sentiment_for_sentence('idiotic and ugly . '),
                         self.cut.get_sentiment_for_sentence('idiotic and ugly'))

    def test_complex_sent_score(self):
        result = self.cut.get_valence_details("i love the dog", True)
        self.assertEqual(result['neg_total'], 0)
        self.assertEqual(result['pos_total'], 3)
        self.assertEqual(result['not_found'], ['i', 'the', 'dog'])

        result = self.cut.get_valence_details("i hate the dog", True)
        self.assertEqual(result['neg_total'], -3)
        self.assertEqual(result['pos_total'], 0)
        self.assertEqual(result['not_found'], ['i', 'the', 'dog'])

        result = self.cut.get_valence_details("love hate", True)
        self.assertEqual(result['neg_total'], -3)
        self.assertEqual(result['pos_total'], 3)
        self.assertEqual(result['absolute_total'], 6)
        self.assertEqual(result['not_found'], [])


    # This is an example on how to use print_result
    def commented_test_print_some_examples(self):
        print("")
        self.cut.print_result("all great things come to an end , and the dot-com era embodies that perfectly")
        self.cut.print_result("beneath a mound of bankruptcy paperwork lies the remains of a former dot-com darling , the company kozmo . com , an online convenience store stocked with ice cream , porn videos , and other basic necessities of a urban dweller , all hand-delivered by couriers within an hour")
        self.cut.print_result("all great things come to an end , and the dot-com era embodies that perfectly", "file1")

if __name__ == "__main__":
    unittest.main()

