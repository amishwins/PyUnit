__author__ = 'Amish'

from read_afin import *
from nltk.parse import earleychart
import runner

class ModalParser():
    def __init__(self):
        self.grammar = nltk.data.load('file:grammar/project3_verbs.fcfg')
        # set "trace = 2" to see the Earley Chart
        self.parser = earleychart.FeatureEarleyChartParser(self.grammar, trace=0)
        self.parsers = dict()
        self.parsers['main'] = self.parser
        self.registered_sentences = list()
        self.afinn = AFINNData()
        self.sent_id = 1

    def parse(self, sentence, parser_name="main"):
        cleaned = self.clean(sentence)
        parses = self.parsers[parser_name].parse(cleaned.split())

        result = dict()
        result['trees'] = [t for t in parses]
        result['num_parses'] = len(result['trees'])
        result['sent'] = sentence

        return result

    # A method which fails gracefully (returns a consumable object)
    def try_parse(self, sentence, parser_name="main"):
        try:
            # in case words are missing from the lexicon
            result = self.parse(sentence, parser_name)
        except ValueError as v:
            result = dict()
            result['trees'] = []
            result['num_parses'] = 0
            result['sent'] = sentence
            print(v)

        return result


    def clean(self, sentence):
        text = sentence
        if text.endswith("."):
            text = text[:-1]

        text = text.replace(" . . . ", " ")
        text = text.replace(" , ", " ")
        text = text.replace("  ", " ")

        return text.strip()

    def register_sentence_with_target(self, sentence, target):
        entry = dict()
        entry['sent_id'] = self.get_next_index()
        entry['sent'] = sentence
        entry['original_file'] = target
        entry['valence_details'] = self.afinn.get_valence_details(sentence)
        entry['afinn'] = self.afinn.get_sentiment_for_sentence(sentence)
        entry['modals'] = self.get_modals(sentence)
        entry['parse_result'] = self.try_parse(sentence)

        self.registered_sentences.append(entry)

    def get_modals(self, sentence):
        result = {}
        modals = ["may", "can", "must", "ought", "will", "shall", "need", "dare", "might", "could", "would", "should"]
        negatives = ["'t", "not"]
        for modal in modals:
            count = len([w for w in list(filter(None, re.split(r"\W+", sentence.lower()))) if w == modal])
            if count > 0:
                result[modal] = count

        return result

    def save_result_file(self):
        output_directory = "output"
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        output_file = os.path.join(output_directory, runner.get_filename_timestamp("post_analysis_"))

        with open(output_file, 'a') as the_file:
            # Write the header
            columns = ['SentID', 'Original_file', 'AFINN', 'AFINN Match Gold', 'ModalPrediction', 'Modal Match Gold',
                       'Modals', '# of modals', 'Pos', 'Neg', 'Sentence']
            the_file.write("\t".join(columns) + "\n")

            for entry in self.registered_sentences:
                modal_ling_prediction = self.get_modal_prediction(entry)

                # Determine if matches "gold standard"
                result_of_afinn = self.get_result(entry, 'afinn')
                result_of_modals = self.get_result(entry, 'modal')

                nice = []
                nice.append(str(entry['sent_id']))
                nice.append(entry['original_file'])
                nice.append(str(float("{0:.5f}".format(entry['afinn']))))
                nice.append(str(result_of_afinn))
                nice.append(modal_ling_prediction)
                nice.append(str(result_of_modals))
                nice.append(str(entry['modals']))
                nice.append(str(len(entry['modals'])))
                nice.append(str(entry['valence_details']['pos']))
                nice.append(str(entry['valence_details']['neg']))
                #nice.append(str(entry['has_negation']))
                nice.append(entry['sent'])
                #print("\t".join(nice))
                the_file.write("\t".join(nice) + "\n")

        os.system('start excel.exe "%s"' % (output_file))

    def get_result(self, entry, modal_or_afinn):
        # TODO: Handle 0 case?
        gold_standard = entry['original_file']

        # This is pretty bad
        if modal_or_afinn == 'afinn':
            if entry['afinn'] > 0 and gold_standard == 'p':
                return True
            elif entry['afinn'] < 0 and gold_standard == 'n':
                return True
            else:
                return False
        elif modal_or_afinn == 'modal':
            modal_prediction = self.get_modal_prediction(entry)
            return modal_prediction == gold_standard

        else:
            raise NameError("Only can compare modal or afinn")

    def display_registered_sentences(self):
        # THIS IS SO BROKEN OMY
        print("%50s %10s %12s %10s %15s" % ('Sentence', 'Gold', 'AFINN SSAP', 'Num Modals', 'ModalLingBeta'))

        for entry in self.registered_sentences:
            modal_ling_prediction = self.get_modal_prediction(entry)
            num_modals = len(entry['modals'])
            #"".format((entry['sent'][:50], entry['original_file'], entry['afinn'], num_modals, modal_ling_prediction))
            #print("%50s %10s %12.2f $2f %15s" % (str(entry['sent'][:50]), str(entry['original_file']), entry['afinn'], str(num_modals), str(modal_ling_prediction)))
            #print(entry['sent'][:50], entry['original_file'], entry['afinn'], num_modals, modal_ling_prediction)

    def get_modal_prediction(self, entry):
        result = ''
        num_modals = len(entry['modals'])
        if num_modals == 0:
            result = "-- no modals --"
        elif entry['parse_result']['num_parses'] == 0:
            result = '** not parsed **'
        else:
            # At this point we assume it was parsed with modals, so for sure we have at least orientation 1, and maybe 2
            sent_structure_label = entry['parse_result']['trees'][0].label()
            orientation_straw_man = self.get_orientation('ORIENTATION', sent_structure_label)
            orientation_real_case = self.get_orientation('ORIENTATION2', sent_structure_label)
            #print(orientation_straw_man, orientation_real_case)
            # It could have been better
            if orientation_straw_man == 'good' and orientation_real_case == None:
                result = 'n'

            # It could have been better, but it was worse
            elif orientation_straw_man == 'good' and orientation_real_case == 'bad':
                result = 'n'

            # It could have been better, but it was better
            elif orientation_straw_man == 'good' and orientation_real_case == 'good':
                result = 'p'

            # It could have been worse
            elif orientation_straw_man == 'bad' and orientation_real_case == None:
                result = 'p'

            # It could have been worse, but it was worse
            elif orientation_straw_man == 'bad' and orientation_real_case == 'bad':
                result = 'n'

            # It could have been worse, but it was better
            elif orientation_straw_man == 'bad' and orientation_real_case == 'good':
                result = 'p'

        return result

    def get_orientation(self, feature, label):
        keys = label.keys()
        if feature in keys:
            return label[feature]
        else:
            return None


    def get_next_index(self):
        result = self.sent_id
        self.sent_id = self.sent_id + 1
        return result

def demo():
    mp = ModalParser()
    mp.register_sentence_with_target('it could be better', 'n')
    mp.register_sentence_with_target('it could be worse', 'p')
    mp.register_sentence_with_target('it should have been better', 'n')
    mp.register_sentence_with_target('it might have been worse', 'p')
    mp.register_sentence_with_target('the movie should have been better', 'n')
    mp.register_sentence_with_target('what might be better is worse', 'n')
    mp.register_sentence_with_target('what could be better is better', 'p')
    mp.register_sentence_with_target('what should be worse is better', 'p')
    mp.register_sentence_with_target('what would be worse is worse', 'n')
    mp.register_sentence_with_target('it might have been better but it was worse', 'n')
    mp.register_sentence_with_target('it could have been worse but it was worse', 'n')
    mp.register_sentence_with_target('it should have been worse but it was better', 'p')
    mp.register_sentence_with_target('it would have been better but it was better', 'p')

    # words missing from lexicon
    mp.register_sentence_with_target('bob hated the movie', 'n')

    # no parses
    mp.register_sentence_with_target('worse worse worse', 'n')

    # modals but no parses
    mp.register_sentence_with_target('worse could have been worse', 'n')

    mp.save_result_file()


class ModalParserTest(unittest.TestCase):
    def setUp(self):
        self.cut = ModalParser()

    def test_object_compiles(self):
        self.assertIsNotNone(self.cut)

    def test_simple_conditional(self):
        expected = {}
        expected['CONDITIONAL'] = True
        expected['TENSE'] = 'pres'
        expected['ORIENTATION'] = 'good'
        self.run_example("it could be better", expected, printTrees=False)

        expected['ORIENTATION'] = 'bad'
        self.run_example("it could be worse", expected, printTrees=False)

    def test_perfect_conditional(self):
        expected = {}
        expected['CONDITIONAL'] = True
        expected['TENSE'] = 'past'
        expected['ORIENTATION'] = 'good'
        self.run_example("it could have been better", expected, printTrees=False)

        expected['ORIENTATION'] = 'bad'
        self.run_example("it could have been worse", expected, printTrees=False)

    def test_harder_nsubj(self):
        expected = {}
        expected['CONDITIONAL'] = True
        expected['TENSE'] = 'past'
        expected['ORIENTATION'] = 'good'
        self.run_example("the movie should have been better", expected, printTrees=False)

    def test_sbar_relative_clause_subj(self):
        expected = {}
        expected['CONDITIONAL'] = True
        expected['TENSE'] = 'pres'
        expected['ORIENTATION'] = 'good'
        expected['ORIENTATION2'] = 'bad'
        self.run_example("what could be better is worse", expected, printTrees=False)

        expected['ORIENTATION'] = 'good'
        expected['ORIENTATION2'] = 'good'
        self.run_example("what should be better is better", expected, printTrees=False)

        expected['ORIENTATION'] = 'bad'
        expected['ORIENTATION2'] = 'good'
        self.run_example("what might be worse is better", expected, printTrees=False)

        expected['ORIENTATION'] = 'bad'
        expected['ORIENTATION2'] = 'bad'
        self.run_example("what would be worse is worse", expected, printTrees=False)

    def test_but_conjunction(self):
        expected = {}
        expected['CONDITIONAL'] = True
        expected['TENSE'] = 'past'
        expected['ORIENTATION'] = 'good'
        expected['ORIENTATION2'] = 'bad'
        self.run_example("it could have been better but it was worse", expected, printTrees=False)

        expected['ORIENTATION'] = 'good'
        expected['ORIENTATION2'] = 'good'
        self.run_example("it should have been better but it was better", expected, printTrees=False)

        expected['ORIENTATION'] = 'bad'
        expected['ORIENTATION2'] = 'bad'
        self.run_example("it would have been worse but it was worse", expected, printTrees=False)

        expected['ORIENTATION'] = 'bad'
        expected['ORIENTATION2'] = 'good'
        self.run_example("it might have been worse but it was better", expected, printTrees=False)

    def test_clean_a_sentence(self):
        self.assertEqual(self.cut.clean("anomie films ."), "anomie films")
        self.assertEqual(self.cut.clean(" . . . jones , despite a definitely "), "jones despite a definitely")
        self.assertEqual(self.cut.clean("jones  , despite a definitely "), "jones despite a definitely")

    def comment_test_first_sentence(self):
        expected = {}
        expected['MODAL'] = "should"
        expected['SEMANTIC'] = "context_neutral"
        self.run_example("jonathan parker's bartleby should have been the be-all-end-all of the modern-office "
                         "anomie films .", expected, printTrees=True)

    def comment_test_first_sentence2(self):
        expected = {}
        expected['MODAL'] = "could"
        expected['SEMANTIC'] = "context_negative"
        expected['TARGET'] = "positive"
        self.run_example("one of those so-so films that could have been much better .", expected, printTrees=True)


    def comment_test_second_sentence(self):
        expected = {}
        expected['MODAL'] = "might"
        expected['SEMANTIC'] = "context_positive"
        self.run_example("what might have been a predictably heartwarming tale is suffused with complexity .",
                         expected, printTrees=True)

    def comment_test_third_sentence(self):
        expected = {}
        expected['MODAL'] = "might"
        expected['SEMANTIC'] = "context_positive"
        self.run_example("what could have been a neat little story about believing in yourself is swamped by "
                         "heavy-handed melodrama .", expected)

    def test_string_replace_replaces_all(self):
        self.assertEqual("a a b a".replace("a", "c"), "c c b c")

    def run_example(self, sentence, expected, isParsable=True, printTrees=True):
        result = self.cut.try_parse(sentence)
        self.process_result(result, isParsable, expected, printTrees)

    def process_result(self, result, isParsable, expected, printTrees=False):
        self.printSimple(result, printTrees)
        if isParsable:
            self.assertTrue(result['num_parses'] > 0, msg=result['sent'])
            for tree in result['trees']:
                labels = tree.label()
                print(labels)
                for key in expected.keys():
                    self.assertEquals(labels[key], expected[key])
        else:
            self.assertTrue(result['num_parses'] == 0, msg=result['sent'])

    def printSimple(self, result, printTrees=False):
        print(result['sent'], "==>", result['num_parses'])
        if printTrees:
            for tree in result['trees']:
                print(tree)

        # only for printing out to paste into the assignment paper
        for tree in result['trees']:
            #print(tree) #print the first tree only
            break
