JDK_ROOT= #your root dir of jdk
HADOOP_ROOT= #your root dir of hadoop
SCALA_ROOT= #your root dir of scala
SPARK_ROOT= #your root dir of spark

export PATH=/usr/local:/ANACONDA_ROOT/bin:JDK_ROOT/bin:$PATH
export LD_LIBRARY_PATH=/OPENBLAS_ROOT/lib:JDK_ROOT/lib:$LD_LIBRARY_PATH
export PYTHONPATH=PYTHON_PACKAGE_DIR/site-packages:$PYTHONPATH
export JAVA_HOME=JDK_ROOT
export HADOOP_HOME=HADOOP_ROOT
export PATH=$PATH:$HADOOP_HOME/bin
export PATH=$PATH:$HADOOP_HOME/sbin
export HADOOP_MAPRED_HOME=$HADOOP_HOME
export HADOOP_COMMON_HOME=$HADOOP_HOME
export HADOOP_HDFS_HOME=$HADOOP_HOME
export YARN_HOME=$HADOOP_HOME
export HADOOP_COMMON_LIB_NATIVE_DIR=$HADOOP_HOME/lib/native
export HADOOP_OPTS="-Djava.library.path=$HADOOP_HOME/lib"

export HADOOP_OPTS="$HADOOP_OPTS -Djava.security.egd=file:/dev/../dev/urandom"
export SCALA_HOME=$SCALA_ROOT
export PATH=$PATH:$SCALA_HOME/bin
export SPARK_HOME=$SPARK_ROOT
export PATH=$PATH:$SPARK_HOME/bin
