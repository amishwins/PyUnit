import nltk
from nltk.parse import earleychart
import os, unittest

class SuperParser:
    def __init__(self):
        self.my_gram = nltk.data.load('file:ut_example.fcfg')
        self.earl = earleychart.FeatureEarleyChartParser(self.my_gram)

    def parse(self, sent):
        result = {}
        parses = self.earl.parse(sent.split())
        result['trees'] = [t for t in parses]
        result['num_parses'] = len(result['trees'])
        return result
   
class TheTests(unittest.TestCase):
    def setUp(self):
        self.class_under_test = SuperParser()

    def test_my_first_test(self):
        result = self.class_under_test.parse("I love cats")
        self.assertEquals(len(result['trees']), 1)

    def test_my_second_better_test(self):
        self.run_example("I love cats", True)
        self.run_example("I cats love", False)

    def run_example(self, sent, is_parsable):
        """ Helper method to aid with unit testing. It allows to create
            simple 1 line tests
        """        
        result = self.class_under_test.parse(sent)
        print(sent, '==>', result['num_parses'])
        if is_parsable:
            self.assertTrue(result['num_parses'] > 0, msg=sent)
        else:
            self.assertTrue(result['num_parses'] == 0, msg=sent)
                                            
if __name__ == "__main__":
    unittest.main(warnings='ignore')

    
