requirements: pyspark(spark environment), nltk, pickle, numpy, scipy

run: SPARK_ROOT/bin/spark-submit index.py --py-files flask.zip,wtforms.zip,nltk.zip

result: start the server and provide search service 