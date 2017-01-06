from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
import pickle
import time
data = open("../../data/corpus.txt", "r").readlines()
documents = [line.strip().split("###")[2] for line in data]
vectorizer = TfidfVectorizer(stop_words="english")
X = vectorizer.fit_transform(documents)
true_k = 100
start_time = time.clock()
model = KMeans(n_clusters=true_k, init='k-means++', max_iter=100, n_init=1)
model.fit(X)
end_time = time.clock()
print "training finished"
print "training time " + str(end_time - start_time)

labels = model.predict(X)
file_out = open("../../data/labels.txt","w")
len1 = labels.shape[0]
for i in xrange(len1):
    file_out.write(str(i) + " " + str(labels[i]) + "\n")
file_out.close()
file_out = open("../../data/cluster.txt", "w")
order_centroids = model.cluster_centers_.argsort()[:, ::-1]
terms = vectorizer.get_feature_names()
for i in range(true_k):
    file_out.write(str(i)+"###")
    for ind in order_centroids[i, :10]:
        file_out.write(terms[ind]+" ")
    file_out.write("\n")
file_out.close()
