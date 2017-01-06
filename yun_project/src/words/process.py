text = open("../../data/corpus.txt", "r").readlines()
words = [val.split("###")[2].strip().split() for val in text]
all_words = dict()
for val in words:
	for val1 in val:
		val1 = val1.lower()
		if all_words.get(val1, ""):
			all_words[val1] += 1
		else:
			all_words[val1] = 1
need_words = []
for val in all_words:
	if all_words[val] > 5 and len(val) > 1:
		need_words.append(val)

word_out = open("../../data/all_words.txt", "w")
for word in need_words:
	word_out.write(word+"\n")
word_out.close()