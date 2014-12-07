__author__ = 'Amish'

from process_sentence_dataset import *
import time
import datetime

def pipeline_runner():
    #Setup
    movieSents = MovieSentences()

    # This should create results for a set # of sentences
    movieSents.register_baseline_results()

    # Apply Semantic Tuning
    #movieSents.apply_semantic_tuning_with_modals_on_baseline()

    # Save the results to a file which we can compare
    #movieSents.persist_results()

def write_analysis_file():
    x = MovieSentences()
    x.load_afinn_for_all_sents()

    sentences = [w for w in x.all_sents_with_afinn if len(w['modals']) > -1]
    print(len(sentences))

    output_directory = "output"

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    output_file = os.path.join(output_directory, get_filename_timestamp())

    with open(output_file, 'a') as the_file:
        # Write the header
        columns = ['SentID', 'Original_file', 'AFINN', 'Modals', '# of modals', 'Pos', 'Neg', 'Has Negation', 'Sentence']
        the_file.write("\t".join(columns) + "\n")

        for sentence in sentences:
            data_object = []
            data_object.append(str(sentence['sent_id']))
            data_object.append(sentence['original_file'])
            data_object.append(str(float("{0:.5f}".format(sentence['afinn']))))
            data_object.append(str(sentence['modals']))
            data_object.append(str(len(sentence['modals'])))
            data_object.append(str(sentence['valence_details']['pos']))
            data_object.append(str(sentence['valence_details']['neg']))
            data_object.append(str(sentence['has_negation']))
            data_object.append(sentence['sent'])
            #print("\t".join(nice))
            the_file.write("\t".join(data_object) + "\n")

    os.system('start excel.exe "%s"' % (output_file))

def get_filename_timestamp(suffix=None):
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d-%H-%M-%S')
    if suffix != None:
        return suffix + st + ".txt"
    else:
        return st + ".txt"