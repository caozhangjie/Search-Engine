from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
import numpy as np
import numpy.matlib as npmat
import scipy as sci
import time

class Kmeans(object):
	def __init__(self, n_clusters, max_iter, threshold=0.01):
		self.n_clusters = n_clusters
		self.max_iter = max_iter
		self.threshold = threshold

	def initialize(self, data):
		threshold_initial = 0.1
		i = 0
		transfer = np.zeros([data.shape[1]])
		self.cluster_centers_[i, :] = data.mean(0)
		temp_data = np.zeros([data.shape[0]])
		index = np.zeros([data.shape[0]])
		for j in xrange(data.shape[0]):
			index[j] = j
		new_list = []
		while i < self.n_clusters-1:
			length = temp_data.shape[0]
			for j in xrange(length):
				temp_data[index[j]] = -np.power((self.cluster_centers_[i, :] - data[index[j], :]), 2).sum()
			sort_index = temp_data.argsort()
			temp_data.sort()
			for x in xrange(length):
				if -temp_data[x] > threshold_initial:
					new_list.append(data[index[sort_index[x]], :])
			i += 1
			self.cluster_centers_[i:(i+1),:] = new_list[0] + transfer


	def fit(self, data):
		self.cluster_centers_ = np.zeros([self.n_clusters, data.shape[1]])
		self.initialize(data)
		parameter_list = []
		data_matrix = np.zeros([data.shape[0]])
		center_matrix = np.zeros([self.n_clusters])
		for i in xrange(data.shape[0]):
			data_matrix[i] = data[i,:].dot(data[i,:].T)[0,0]

		for k in xrange(self.max_iter):
			for i in xrange(self.n_clusters):
				center_matrix[i] = np.dot(self.cluster_centers_[i,:], self.cluster_centers_[i,:].T)
			diff_matrix = data.dot(self.cluster_centers_.T)
			for i in xrange(data.shape[0]):
				for j in xrange(self.n_clusters):
					diff_matrix[i, j] = data_matrix[i] + center_matrix[j] - 2 * diff_matrix[i, j]

			new_labels = np.argsort(diff_matrix, axis=1)
			old_centers = self.cluster_centers_
			self.cluster_centers_ = np.zeros([self.n_clusters, data.shape[1]])
			num_instances = np.zeros([self.n_clusters])
			for i in xrange(data.shape[0]):
				self.cluster_centers_[int(new_labels[i][0]), :] = data[i,:] + self.cluster_centers_[int(new_labels[i][0]), :]
				num_instances[int(new_labels[i][0])] += 1
			for i in xrange(self.n_clusters):
				if num_instances[i] > 0:
					self.cluster_centers_[i, :] /= float(num_instances[i])
			diff = np.sum(np.power(old_centers - self.cluster_centers_, 2))
			if diff < self.threshold:
				break
		self.center_matrix = center_matrix


	def predict(self, data):
		length = data.shape[0]
		label_list = []
		data_matrix = np.zeros([data.shape[0]])
		for i in xrange(length):
			data_matrix[i] = data[i,:].dot(data[i,:].T)[0,0]
		diff_matrix = data.dot(self.cluster_centers_.T)
		for i in xrange(length):
			for j in xrange(self.n_clusters):
				diff_matrix[i, j] = data_matrix[i] + self.center_matrix[j] - 2 * diff_matrix[i, j]
		new_labels = np.argsort(diff_matrix, axis=1)
		for i in xrange(length):
			label_list.append(int(new_labels[i][0]))
		return np.array(label_list)


data = open("../../data/corpus.txt", "r").readlines()
documents = [line.strip().split("###")[2] for line in data]
vectorizer = TfidfVectorizer(stop_words="english")
X = vectorizer.fit_transform(documents)
true_k = 5
start_time = time.clock()
model = Kmeans(true_k, 100)
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
