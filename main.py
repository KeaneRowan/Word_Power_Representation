# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from transformers import AutoConfig, AutoModelForSequenceClassification


def train_val_test_split(file_path):
    import random
    file = open(file_path, encoding="utf-8")
    data = file.readlines()
    trainx = []
    trainy = []
    valx = []
    valy = []
    testx = []
    testy = []
    TRAIN_CONST = int(.8 * len(data))
    VAL_CONST = int(.1 * len(data))
    TEST_CONST = int(.1 * len(data))
    for i in range(0, TEST_CONST):
        randomnum = random.randrange(0, len(data))
        currdata = data[randomnum].split(",")
        testx.append(currdata[1])
        testy.append(currdata[2].strip())
        data.remove(data[randomnum])
    for i in range(0, VAL_CONST):
        randomnum = random.randrange(0, len(data))
        currdata = data[randomnum].split(",")
        valx.append(currdata[1])
        valy.append(currdata[2].strip())
        data.remove(data[randomnum])
    for i in range(0, TRAIN_CONST):
        randomnum = random.randrange(0, len(data))
        currdata = data[randomnum].split(",")
        trainx.append(currdata[1])
        trainy.append(currdata[2].strip())
        data.remove(data[randomnum])
    return trainx, trainy, valx, valy, testx, testy

def train_model():
    #https://towardsdatascience.com/fine-tuning-hugging-face-model-with-custom-dataset-82b8092f5333 is where I learned how to construct tokenizer to feed into distilbert model
    from transformers import DistilBertTokenizerFast
    from transformers import TFDistilBertForSequenceClassification
    import tensorflow as tf
    trainx, trainy, valx, valy, testx, testy = train_val_test_split(r"Rankings/AutoGeneratedRankings.txt")
    #trainx = str(trainx)
    trainy = list(map(int, trainy))
    #valx = str(valx)
    valy = list(map(int, valy))
    testx = str(testx)
    testy = str(testy)
    tokenizer = DistilBertTokenizerFast.from_pretrained('distilbert-base-uncased')
    train_encodings = tokenizer(trainx,
                                truncation=True,
                                padding=True)
    val_encodings = tokenizer(valx,
                              truncation=True,
                              padding=True)
    test_encodings = tokenizer(testx,
                              truncation=True,
                              padding=True)
    train_dataset = tf.data.Dataset.from_tensor_slices((
        dict(train_encodings),
        trainy
    ))
    val_dataset = tf.data.Dataset.from_tensor_slices((
        dict(val_encodings),
        valy
    ))
    #We need 101 predictions to cover values 0 to 100
    model = TFDistilBertForSequenceClassification.from_pretrained("Model_Versions/word_power_model")
    optimizer = tf.keras.optimizers.Adam(learning_rate=5e-5)
    model.compile(optimizer=optimizer, loss=model.compute_loss, metrics=['accuracy'])
    model.fit(train_dataset.shuffle(100).batch(32),
              epochs=30,
              batch_size=32,
              validation_data=val_dataset.shuffle(100).batch(32))
    model.save_pretrained("Model_Versions/word_power_model")
def get_max_index(arr):
    index = 0
    maxval = 0
    for i in range(0, len(arr)):
        if arr[i] > maxval:
            maxval = arr[i]
            index = i
    return index

def create_new_points(data, tags):
    import tensorflow
    from transformers import DistilBertTokenizerFast
    from transformers import TFDistilBertForSequenceClassification
    loaded_model = TFDistilBertForSequenceClassification.from_pretrained("Model_Versions/word_power_model")
    tokenizer = DistilBertTokenizerFast.from_pretrained('distilbert-base-uncased')
    file = open(r"Rankings/AutoGeneratedRankings.txt", "a", encoding = "utf-8")
    for i in range(0, len(data)):
        predict_input = tokenizer.encode(data[i],
                                         truncation=True,
                                         padding=True,
                                         return_tensors="tf")
        tf_output = loaded_model.predict(predict_input)[0]
        tf_prediction = tensorflow.nn.softmax(tf_output, axis=1).numpy()[0]
        file.write("\n" + tags[i] + "," + str(data[i]) + "," + str(get_max_index(tf_prediction)))



def generate_more_data(numData):
    import spacy
    from sense2vec import Sense2Vec
    import numpy
    import pandas as pd
    import keras
    from random import randrange
    from datetime import time
    from keras.layers import Conv1D, Dropout, MaxPooling1D, Flatten, Dense
    import os
    nlp = spacy.load("en_core_web_lg")
    s2v = nlp.add_pipe("sense2vec")
    s2v.from_disk("spaCyVectors//s2v_old")
    allwords = list(nlp.vocab.strings)
    allusedwords = []
    file = open("Rankings//AutoGeneratedRankings.txt")
    allusedwords = pd.read_csv("Rankings//AutoGeneratedRankings.txt", header=None, delim_whitespace=False)
    allusedwords = allusedwords.values
    all_of_our_used_lemmas = []
    for data in allusedwords:
        all_of_our_used_lemmas.append(data[0])
    # We start picking words at random here
    i = 0
    new_words = []
    while i < numData:
        randomnum = randrange(0, len(allwords))
        word = allwords[randomnum]
        if word not in all_of_our_used_lemmas and word.isalpha():
            doc = nlp(word)
            if numpy.any(doc[0]._.s2v_vec):
                numData -= 1
                file = open("Rankings//temp.txt", 'a', encoding='utf-8')
                for i in range(0, len(doc)):
                    file.write(str(doc[i]._.s2v_key).split("|")[0] + ",")
                    for num in doc[0]._.s2v_vec:
                        file.write(str(num) + " ")
                    file.write(",\n")
                file.close()
    newData = pd.read_csv("Rankings//temp.txt", header=None, delim_whitespace=False).values
    vals_to_predict = []
    actual_vals = []
    for item in newData:
        vals_to_predict.append(item[1])
        actual_vals.append(item[0])
    if os.path.isfile("Rankings//temp.txt"):
        os.remove("Rankings//temp.txt")
    create_new_points(vals_to_predict, actual_vals)
# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    train_model()


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
