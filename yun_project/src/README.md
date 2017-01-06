All the sub README.md are in the corresponding directory.  

usages:

1\First install all the requirements and hadoop, spark environments, the configuration file can be found in env directory. After downloading Hadoop 2.7 and Spark 2.0.1 and unzipping them in any node of one cluster, copy files under env/hadoop directory into hadoop/etc/hadoop. Then copy files under env/spark/conf directory into spark/conf. Thirdly copy files under ~/.bashrc directory as ~/.bashrc on your server. Finally copy these unzipped directories to all nodes in the cluster.

2\crawl and preprocess data: follow the README.md in spider,words and cluster directories sequentially 

3\put all the ".txt" files to hadoop file system

4\set hadoop_save_dir variable in "server/index.py" file as the dir of the previous step
   set master setting of your own spark
   set host_ip as the ip of your server

5\run server: follow the README.md in server directory
