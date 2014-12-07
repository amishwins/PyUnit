__author__ = 'Amish'

from read_afin import *
from collections import Counter


# Sentence Sentiment (Announcement November 5, 2014)
class MovieSentences:
    def __init__(self):
        self.afinn = AFINNData()
        self.neg_path = os.path.join('..', 'rt-polarity', 'rt-polaritydata', 'rt-polarity.neg')
        self.pos_path = os.path.join('..', 'rt-polarity', 'rt-polaritydata', 'rt-polarity.pos')
        self.upper_threshold = 1.5
        self.lower_threshold = -1

        # this isn't good - temporal coupling :(
        self.utterance_index = 1

        self.neg_sents = self.load_sents(self.neg_path)
        self.pos_sents = self.load_sents(self.pos_path)

        self.all_sents_with_afinn = []

        # Baseline using AFINN
        self.pos_sent_with_neg_afinn = [(w, self.afinn.get_sentiment_for_sentence(w)) for w in self.pos_sents
                                        if self.afinn.get_sentiment_for_sentence(w) < 0]

        self.neg_sent_with_pos_afinn = [(w, self.afinn.get_sentiment_for_sentence(w)) for w in self.neg_sents
                                        if self.afinn.get_sentiment_for_sentence(w) > 0]

        self.neutral_neg_sent_afinn = [(w, 'n') for w in self.neg_sents
                                       if self.afinn.get_sentiment_for_sentence(w) == 0]

        self.neutral_pos_sent_afinn = [(w, 'p') for w in self.pos_sents
                                       if self.afinn.get_sentiment_for_sentence(w) == 0]

        self.all_neutrals = self.neutral_neg_sent_afinn + self.neutral_pos_sent_afinn

        self.neutrals_with_absolutes = self.get_result_with_absolute_score_and_modals()

        self.original_baseline = []

    # Made this a load function, because if called during initialization it's very slow for all unit tests
    # Is this good design?
    def load_afinn_for_all_sents(self):
        if len(self.all_sents_with_afinn) == 0:
            neg = self.get_afinn_for_sents('n')
            pos = self.get_afinn_for_sents('p')
            self.all_sents_with_afinn = neg + pos
        else:
            print("AFINN for all sents registered")

    def save_data(self, object_to_save, filename):
        output_directory = "output"

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        output_file = os.path.join(output_directory, filename + ".json")
        with open(output_file, 'w') as js:
            json.dump(object_to_save, js, indent=4, sort_keys=True)

    def get_next_index(self):
        result = self.utterance_index
        self.utterance_index = self.utterance_index + 1
        return result

    def get_afinn_for_sents(self, original_file):
        results = list()

        if original_file == 'n':
            list_to_use = self.neg_sents
        elif original_file == 'p':
            list_to_use = self.pos_sents
        else:
            raise NameError("Wrong file type:", original_file)

        for sent in list_to_use:
            result = dict()
            result['sent_id'] = self.get_next_index()
            result['sent'] = sent
            result['original_file'] = original_file
            result['afinn'] = self.afinn.get_sentiment_for_sentence(sent)
            result['valence_details'] = self.afinn.get_valence_details(sent, store_not_found=False)
            result['modals'] = self.get_modals(sent)
            result['has_negation'] = self.has_negation(sent)
            results.append(result)

        return results

    # Some helper methods
    def get_data_in_range(self, threshold, positive=True):
        data = [w['afinn'] for w in self.all_sents_with_afinn]
        min_afinn = min(data)
        max_afinn = max(data)
        #print(min_afinn)
        #print(max_afinn)

        if positive:
            data = [w for w in self.all_sents_with_afinn if w['afinn'] >= threshold]
        else:
            data = [w for w in self.all_sents_with_afinn if w['afinn'] <= threshold]

        return data


    def get_result_with_absolute_score_and_modals(self):
        results = []

        for neutral in self.all_neutrals:
            result = dict()
            result['sent'] = neutral[0]
            result['original_file'] = neutral[1]
            result['valence_details'] = self.afinn.get_valence_details(neutral[0])
            result['modals'] = self.get_modals(neutral[0])
            result['sentiment_evaluation'] = ""
            results.append(result)

        return results

    def get_modals(self, sentence):
        result = {}
        modals = ["may", "can", "must", "ought", "will", "shall", "need",
                  "dare", "might", "could", "would", "should"]
        negatives = ["'t", "not"]
        for modal in modals:
            count = len([w for w in list(filter(None, re.split(r"\W+", sentence.lower()))) if w == modal])
            if count > 0:
                result[modal] = count

        return result

    def has_negation(self, sent):
        negators = ['not', "can't", "didn't", "wouldn't", "shouldn't", "couldn't", 'but', 'cannot']
        for negator in negators:
            if self.find_whole_word(negator)(sent):
                return True

        return False

    def find_whole_word(self, word):
        return re.compile(r'\b({0})\b'.format(word), flags=re.IGNORECASE).search

    def get_linguistic_fun(self, baseline):
        result = {}
        result['wordlist'] = []

        for sent in [s[0] for s in baseline]:
            for word in sent.split():
                result['wordlist'].append(word)

        result['text'] = nltk.Text(result['wordlist'])
        result['fd'] = nltk.FreqDist(result['text'])
        return result

    def get_sents_from_all_neutrals_with_words(self, words):
        return [w for w in self.all_neutrals if words in w[0]]

    def summarize_baseline(self):
        print("False positives %4s %6.2f" %
              (len(self.pos_sent_with_neg_afinn), (len(self.pos_sent_with_neg_afinn) / len(self.pos_sents)) * 100))
        print("False negatives %4s %6.2f" %
              (len(self.neg_sent_with_pos_afinn), (len(self.neg_sent_with_pos_afinn) / len(self.neg_sents)) * 100))

    def load_sents(self, the_path):
        with open(the_path, 'r') as f:
            lines = re.split(r'\n', f.read())
            return lines

        # problem with utf-8 :( boo
#        with codecs.open(the_path, 'r', encoding='utf8') as f:
#            lines = re.split(r'\n', f.read())
#            return lines

    def get_positive_sents_with_negative_afinn(self, rating):
        low = [w for w in self.pos_sent_with_neg_afinn if w[1] < rating]
        return low

    def display_list_nicely(self, sents_and_afinn):
        for entry in sents_and_afinn:
            print("%5.2f %s" % (entry[1], entry[0]))


class MovieSentencesTests(unittest.TestCase):
    def setUp(self):
        self.cut = MovieSentences()

    def test_files_have_good_endings(self):
        self.assertTrue(self.cut.neg_path.endswith('.neg'))
        self.assertTrue(self.cut.pos_path.endswith('.pos'))

    def test_files_have_good_length(self):
        self.assertEqual(len(self.cut.neg_sents), 5332)
        self.assertEqual(len(self.cut.pos_sents), 5332)

    def test_baseline_values(self):
        self.assertEqual(len(self.cut.pos_sent_with_neg_afinn), 812)
        self.assertEqual(len(self.cut.neg_sent_with_pos_afinn), 1968)
        self.assertEqual(len(self.cut.neutral_neg_sent_afinn), 1530)
        self.assertEqual(len(self.cut.neutral_pos_sent_afinn), 1307)
        self.assertEqual(len(self.cut.all_neutrals), 2837)


    def test_positive_sent_low_neg(self):
        self.assertEqual(len(self.cut.get_positive_sents_with_negative_afinn(-2)), 5)
        self.assertEqual(len(self.cut.get_positive_sents_with_negative_afinn(-1)), 88)
        self.assertEqual(len(self.cut.get_positive_sents_with_negative_afinn(-0.5)), 364)
        self.assertEqual(len(self.cut.get_positive_sents_with_negative_afinn(0)), 812)

    def test_freq_dist_is_not_null(self):
        self.assertIsNotNone(self.cut.get_linguistic_fun(self.cut.neutral_neg_sent_afinn))
        self.assertIsNotNone(self.cut.get_linguistic_fun(self.cut.neutral_neg_sent_afinn)['fd'])

    def test_get_absolutes_and_modals(self):
        self.assertIsNotNone(self.cut.neutrals_with_absolutes)
        self.assertEqual(len(self.cut.neutrals_with_absolutes), 2837)
        self.assertEqual(len([r for r in self.cut.neutrals_with_absolutes if r['valence_details']['absolute_total'] == 0]), 2354)

        # Sentences which have an absolute_valence of not 0 (meaning even though the sum was 0, some words had AFINN values
        non_absolute_zero_sents = [r for r in self.cut.neutrals_with_absolutes if r['valence_details']['absolute_total'] != 0]
        self.assertEqual(len(non_absolute_zero_sents), 483)

        for sent in non_absolute_zero_sents:
            if len(sent['modals'].keys()) > 0:
                toprint = []
                toprint.append(sent['modals'])
                toprint.append(sent['valence_details']['pos_total'])
                toprint.append(sent['valence_details']['neg_total'])
                toprint.append(sent['valence_details']['absolute_total'])
                toprint.append(sent['sent'])
                #print(toprint)

    def test_get_modals(self):
        modals = self.cut.get_modals("would would could could can must will")
        self.assertEqual(modals['would'], 2)
        #print(modals.keys())

    def test_metrics_for_all_sents(self):
        self.cut.load_afinn_for_all_sents()
        all_sents = [w['sent'] for w in self.cut.all_sents_with_afinn]
        all_words = re.split(r"\W+", " ".join(all_sents))
        print("All words:", len(all_words))
        print("Unique words: ", len(set(all_words)))


    def test_extremes(self):
        self.cut.load_afinn_for_all_sents()
        data = self.cut.get_data_in_range(1.5, True)
        from_neg = [w for w in data if w['original_file'] == 'n']
        with_modals = [w for w in from_neg if len(w['modals']) > 0]
        #print(len(data), len(from_neg), len(with_modals))
        #for entry in with_modals:
        #    print(entry)

        data = self.cut.get_data_in_range(-1, False)
        from_pos = [w for w in data if w['original_file'] == 'p']
        with_modals = [w for w in from_pos if len(w['modals']) > 0]
        #print(len(data), len(from_pos), len(with_modals))
        #for entry in with_modals:
        #    print(entry)


    def test_has_negation(self):
        sent = "I didn't love him"
        self.assertEqual(self.cut.has_negation(sent), True)

        sent = "It was great, but I hated it."
        self.assertEqual(self.cut.has_negation(sent), True)

        sent = "I did not enjoy it"
        self.assertEqual(self.cut.has_negation(sent), True)

        sent = "Wouldn't"
        self.assertEqual(self.cut.has_negation(sent), True)

        sent = "I loved Benjamin Button"
        self.assertEqual(self.cut.has_negation(sent), False)

        sent = "I would've enjoyed it"
        self.assertEqual(self.cut.has_negation(sent), False)


    def test_modals(self):
#        res = self.cut.get_linguistic_fun(self.cut.all_neutrals)
        #may, can, must, ought, will, shall, need, dare, might, could, would, and should
        self.display_modal_count("may")
        self.display_modal_count("may not")
        self.display_modal_count("can")
        self.display_modal_count("cannot")
        self.display_modal_count("can't")
        self.display_modal_count("must")
        #self.display_modal_count("must not")
        self.display_modal_count("ought")
        #self.display_modal_count("ought not")
        self.display_modal_count("will")
        self.display_modal_count("will not")
        #self.display_modal_count("won't")
        self.display_modal_count("shall")
        #self.display_modal_count("shall not")
        self.display_modal_count("need")
        #self.display_modal_count("need not")
        self.display_modal_count("dare")
        #self.display_modal_count("dare not")
        self.display_modal_count("might")
        self.display_modal_count("might not")
        self.display_modal_count("could")
        #self.display_modal_count("could not")
        self.display_modal_count("couldn't")
        self.display_modal_count("would")
        #self.display_modal_count("would not")
        self.display_modal_count("wouldn't")
        self.display_modal_count("should")
        #self.display_modal_count("should not")
        self.display_modal_count("shouldn't")

    def display_modal_count(self, modal):
        result = self.cut.get_sents_from_all_neutrals_with_words(modal)
        #print("%10s %3s %3s %3s" % (modal, len(result), len([w for w in result if w[1] == 'n']), len([w for w in result if w[1] == 'p'])))


if __name__ == "__main__":
    unittest.main()
