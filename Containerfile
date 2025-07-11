FROM docker.io/apache/hadoop:3.4 AS hadoop_base

ENV HADOOP_HOME /opt/hadoop
ENV HADOOP_CONF_DIR ${HADOOP_HOME}/etc/hadoop

USER root
ENTRYPOINT []

########################################
FROM hadoop_base AS hadoop_name_node
COPY start_name_node.sh /start_name_node.sh
RUN chmod +x /start_name_node.sh
CMD [ "/start_name_node.sh" ]

########################################
FROM hadoop_base AS hadoop_data_node
COPY start_data_node.sh /start_data_node.sh
RUN chmod +x /start_data_node.sh
CMD [ "/start_data_node.sh" ]

########################################
FROM docker.io/spark:4.0.0 AS spark_base
ENV SPARK_NO_DAEMONIZE true

ENV HADOOP_HOME /opt/hadoop
ENV HADOOP_CONF_DIR ${HADOOP_HOME}/etc/hadoop

##########################################
FROM spark_base AS spark_master
CMD [ "/opt/spark/sbin/start-master.sh" ]

##################################
FROM spark_base AS spark_worker
CMD [ "/opt/spark/sbin/start-worker.sh" ]

##########################################
FROM spark_base AS spark_history_server
CMD [ "/opt/spark/sbin/start-history-server.sh" ]

##########################################
FROM spark_base AS spark_connect
CMD [ "/opt/spark/sbin/start-connect-server.sh" ]

FROM scratch AS default
ENTRYPOINT [ "use-nondefault-targets-instead" ]
