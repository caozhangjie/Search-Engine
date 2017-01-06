from pyspark import SparkContext, SparkConf
import nltk
from pyspark.mllib.feature import HashingTF, IDF
from pyspark.storagelevel import StorageLevel
from pyspark.mllib.linalg import SparseVector
import nltk.data
import pickle
from nltk.stem.lancaster import LancasterStemmer
from nltk.tokenize import MWETokenizer
import numpy as np
import scipy as sci
import scipy.sparse as scisparse
import re
import time
import random
from flask import Flask, render_template, flash, request,jsonify, Response, json
from wtforms import Form, TextField, TextAreaField, validators, StringField,SubmitField

#app config
#set your own hadoop dir where you save the data files in the previous steps
hadoop_save_dir = ""
#master port
master_setting = ""
#ip of server
host_ip = ""

DEBUG = False
app = Flask(__name__, static_url_path='/static')
app.config.from_object(__name__)
s_conf = SparkConf().set("spark.driver.maxResultSize", "2g").setMaster("spark://"+master_setting).setAppName("Calculate")
st = SparkContext(conf=s_conf)

default_sent_tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
default_st = LancasterStemmer()
default_phrase_dict = pickle.load(open("./phrase_dict.pkl", "r"))
default_mwetokenizer = MWETokenizer(default_phrase_dict)

def processCorpus(line):
    d = line.strip().split("###")
    temp = d[2].split()
    text_c = filter(lambda x: x.isalnum(), temp)
    return text_c

def processText(line):
    d = line.strip().split("###")
    return (int(d[0]), d[2])

def processTitle(line):
    d = line.strip().split("###")
    return (int(d[0]), d[1])

def processWords(line):
    return line.strip().split()

def filterWords(word_dict):
    def filterWord(line):
        lines = line.strip().split("###")
        word_doc = []
        temp_dict = dict()
        if len(lines) > 2:
            words = lines[2].split()
            for val in words:
                if word_dict.get(val, "") and (not temp_dict.get(val, "")):
                    word_doc.append((val, int(lines[0])))
                    temp_dict[val] = 1
        return word_doc
    return filterWord

def processTF(line):
    indices = line.indices
    values = line.values
    len1 = indices.shape[0]
    if len1 > 0:
        max_tf = float(values.max())
        new_values = values / max_tf
        index_all = []
        for i in xrange(len1):
            index_all.append([indices[i], new_values[i]])
        return SparseVector(line.size, index_all)
    else:
        return SparseVector(line.size, [])

def processQueryTF(line):
    indices = line.indices
    len1 = indices.shape[0]
    new_values = [1.0 for i in xrange(len1)]
    if len1 > 0:
        return scisparse.csr_matrix((new_values, indices, [0, len1]), (1, line.size))
    else:       
        return scisparse.csr_matrix((1, line.size))


def processTFIDF(max_idf):
    def innerfunc(line):
        indices = line.indices
        values = line.values
        len1 = indices.shape[0]
        if len1 > 0:
            new_values = values / max_idf
            return scisparse.csr_matrix((new_values, indices, [0, len1]), (1, line.size))
        else:
            return scisparse.csr_matrix((1, line.size))
    return innerfunc




def getIndex(word):
    global inverted_index
    find_index = inverted_index.filter(lambda line: True if word.get(line[0], "") else False).flatMap(lambda line: [(val, line[0]) for val in line[1]]).groupByKey()
    return find_index

def getSimilarity(query_vector, sum_):
    def calculate(line):
        return 1.0 - np.sqrt(((line - query_vector).power(2).multiply(query_vector)).sum() / sum_)
    return calculate


def getOrderedList(valid_words):
    global hashingTF
    global idf
    global st
    global max_idf
    query_rdd = st.parallelize(valid_words)
    tf_query_raw = hashingTF.transform(query_rdd)
    tf_query = tf_query_raw.map(processQueryTF).collect()[0]
    sum_ = float(tf_query.sum())
    similarity = tfidf.map(getSimilarity(tf_query, sum_)).collect()
    pair_list = []
    len1 = len(similarity)
    for i in xrange(len1):
        pair_list.append((i, url_dict[i], similarity[i]))
    return sorted(pair_list, key=lambda item: item[2], reverse=True)
 
def getIndexAndResult(input_str):
    global word_dict
    query_words = nltk.word_tokenize(input_str)
    valid_words = []
    valid_words_dict = dict()
    for val in query_words:
        if word_dict.get(val, ""):
            valid_words.append(val)
            valid_words_dict[val] = 1
    find_index = getIndex(valid_words_dict)
    ordered_list = getOrderedList([valid_words])
    return (ordered_list, find_index)
 
def highlight(doc_id_word):
    def innerFunc(line):
        word_iter = doc_id_word.get(line[0], "")
        temp_index = []
        if word_iter:
            for val_word in word_iter:
                temp_index = temp_index + [(val.start(), val.end()) for val in re.finditer(val_word, line[1])]
        return temp_index
    return innerFunc

def searchForResult(input_str, start_index, end_index):
    global title_content
    global text_content
    result = getIndexAndResult(input_str)
    need_id = {val[0]:1 for val in result[0][start_index:end_index]}
    order_id = [val[0] for val in result[0][start_index:end_index]]
    contain_word_list = result[1].filter(lambda line: True if need_id.get(line[0], "") else False).collect()
    contain_word_dict = {val[0]:val[1] for val in contain_word_list}
    return_url = [val[1] for val in result[0][start_index:end_index]]
    return_title = []
    return_text = []
    title_label = []
    text_label = []
    for val in order_id:
        return_title.append(title_content.filter(lambda line: line[0] == val).collect()[0][1])
        return_text.append(text_content.filter(lambda line: line[0] == val).collect()[0][1])
        title_label.append(title_content.filter(lambda line: line[0] == val).map(highlight(contain_word_dict)).collect())
        text_label.append(text_content.filter(lambda line: line[0] == val).map(highlight(contain_word_dict)).collect())
    return [result, return_url, return_title, return_text, title_label, text_label]

def searchWithResult(result, start_index, end_index):
    global title_content
    global text_content
    need_id = {val[0]:1 for val in result[0][start_index:end_index]}
    order_id = [val[0] for val in result[0][start_index:end_index]]
    contain_word_list = result[1].filter(lambda line: True if need_id.get(line[0], "") else False).collect()
    contain_word_dict = {val[0]:val[1] for val in contain_word_list}
    return_url = [val[1] for val in result[0][start_index:end_index]]
    return_title = []
    return_text = []
    title_label = []
    text_label = []
    for val in order_id:
        return_title.append(title_content.filter(lambda line: line[0] == val).collect()[0][1])
        return_text.append(text_content.filter(lambda line: line[0] == val).collect()[0][1])
        title_label.append(title_content.filter(lambda line: line[0] == val).map(highlight(contain_word_dict)).collect())
        text_label.append(text_content.filter(lambda line: line[0] == val).map(highlight(contain_word_dict)).collect())
    return [return_url, return_title, return_text, title_label, text_label]

def getLabels(doc_id, num):
    global id_to_label
    global clusters_name
    class_id = id_to_label.filter(lambda line: line[0] == doc_id).collect()[0][1]
    cluster_name = clusters_name.filter(lambda line: line[0] == class_id).collect()[0][1]
    temp_similar_id = id_to_label.filter(lambda line: line[1] == class_id).collect()
    similar_id = [val[0] for val in temp_similar_id]
    return_values = []
    for val in xrange(num):
        id_ = similar_id[val]
        return_values.append({"title":title_content.filter(lambda line: line[0] == id_).collect()[0][1], "url":url_dict[id_], "cluster_name":cluster_name})
    return return_values

@app.route('/query/changePages', methods=['GET','POST'])
def changePages():
    form = ReusableForm(request.form)
    print form.errors
    if request.method == 'POST':
        searchContent = request.values.get('searchContent', 0, type=str)
        pageNumber = request.values.get('page', 0, type=int) 
        print pageNumber
        searchResult = searchWithResult(result, 20 * (pageNumber - 1), 20 * pageNumber)
        searchResultList = []
        print(len(searchResult[0]))
        for i in xrange(len(searchResult[1])):
            temp = {}
            temp["url"] = searchResult[0][i]
            temp["title"] = searchResult[1][i]
            temp["content"] = searchResult[2][i]
            temp["text-label"] = searchResult[4][i]
            searchResultList.append(temp)
        labels = getLabels(result[0][0][0],100)
        return Response(json.dumps(searchResultList),mimetype="application/json")

@app.route('/query', methods=['GET', 'POST'])
def getQueryAndSearch():
    global result
    form = ReusableForm(request.form)
    print form.errors
    if request.method == 'POST':
        searchContent = request.form['searchContent']
        searchResult = searchForResult(searchContent, 0, 20)
        result = searchResult[0]
        searchResultList = []
        for i in xrange(len(searchResult[1])):
            temp = {}
            temp["url"] = searchResult[1][i]
            temp["title"] = searchResult[2][i]
            temp["content"] = searchResult[3][i]
            temp["text-label"] = searchResult[5][i]
            searchResultList.append(temp)
        labels =  getLabels(result[0][0][0], 100)
        cluster_name = labels[0]["cluster_name"]

        return render_template('result.html', form=form, searchContent=searchContent, searchResult=searchResultList, labels=labels, cluster_name=cluster_name)

@app.route('/')
def hello_world():
    form = ReusableForm(request.form)
    return render_template('index.html', form=form)

if __name__ == "__main__":
    #read in file
    word_file = st.textFile("hdfs://"+hadoop_save_dir+"/all_words.txt")
    txt_file = st.textFile("hdfs://"+hadoop_save_dir+"/corpus.txt")
    title_file = st.textFile("hdfs://"+hadoop_save_dir+"/titles.txt")
    text_file = st.textFile("hdfs://"+hadoop_save_dir+"/corpus_text.txt")
    label_file = st.textFile("hdfs://"+hadoop_save_dir+"/labels.txt")
    cluster_file = st.textFile("hdfs://"+hadoop_save_dir+"/cluster.txt")

    text_content = text_file.map(processText).persist(StorageLevel.MEMORY_AND_DISK)
    title_content = title_file.map(processTitle).persist(StorageLevel.MEMORY_AND_DISK)
    id_to_label = label_file.map(lambda line: (int(line.strip().split()[0]), int(line.strip().split()[1])))
    clusters_name = cluster_file.map(lambda line: (int(line.strip().split("###")[0]), line.strip().split("###")[1]))
   
    #get url list
    url_dict = []
    url_file = open("../../data/corpus.txt", "r").readlines()
    for val in url_file:
        d = re.split("###", val.strip())
        url = d[1]
        url_dict.append(url)
    doc_num = len(url_dict)
    #calculate TF-IDF feature
    word_dict_size = 504927
    hashingTF = HashingTF(word_dict_size)
    tf_words = hashingTF.transform(word_file.map(processWords))
    tf_raw = hashingTF.transform(txt_file.map(processCorpus))
    idf = IDF().fit(tf_raw)
    max_idf = float(idf.idf().max())
    tf = tf_raw.map(processTF)
    tfidf = idf.transform(tf).map(processTFIDF(max_idf))
    tfidf.persist(StorageLevel.MEMORY_AND_DISK)
    tf.persist(StorageLevel.MEMORY_AND_DISK)
    tf_raw.persist(StorageLevel.MEMORY_AND_DISK)
    
    #get word dictionary
    words_all = open("../../data/all_words.txt", "r").readlines()
    words_all = [val.strip() for val in words_all]
    word_dict = {val:1 for val in words_all}
    
    #get inverted index
    temp1 = txt_file.map(filterWords(word_dict))
    temp2 = temp1.flatMap(lambda line: line)
    inverted_index = temp2.groupByKey()
    inverted_index.cache()

    result = None
    app.run(host=host_ip,port=5000)

