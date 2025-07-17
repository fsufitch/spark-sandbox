# Spark Sandbox

Need to run Spark in a sandbox environment? This is the place to do it.

This repository contains a collection of scripts and configurations to set up a Spark environment quickly, using Docker Compose or a similar tool. **This is not a production-ready setup**; it's meant for development and testing purposes only.

> **Note:** The filenames of various container tech uses are the "generic" non-Docker variants. This is because the project was coded using rootless Podman. As such, the usage recipes also contain `podman` and `podman-compose` commands. If you are using Docker, you can simply replace these with `docker` and `docker-compose`, but may need to add `-f compose.yaml` if Docker Compose does not recognize it by default.

## Usage "Recipes"

### Build the relevant container images

```bash
podman-compose build
```

### Start the cluster

```bash
podman-compose up -d
```

`-d` is used to run the containers in detached mode. This is better than not, as it means the cluster will survive your terminal closing. It also lends itself more easily to monitoring the logs using `podman-compose logs ...` for a specific container, as the default "multiplexed" log stream is quite overwhelming.

### Grant unauthenticated access to the Hadoop FS

This setup does not use any authentication for the Hadoop File System (HDFS). This is done to simplify the setup and allow easy access to the files stored in HDFS. However, this is not recommended for production environments, as it poses a security risk.

The default Hadoop setup does not allow users to write to the HDFS root directory. To allow this, you need to run the following command:

```bash
podman exec hadoop-name1 hdfs dfs -chmod 777 /
```

### Stop the cluster

```bash
podman-compose down
```

This not only stops the containers, but also removes them, plus other resources related to them (such as the container network). This is in line with container best practices, which recommend containers be ephemeral and not persist data across runs.

Data is persisted using volumes, which are not removed by this command. If you want to remove the volumes as well, you can use:

```bash
podman-compose down -v
```

### Monitor status of containers

```bash
podman-compose ps
```

## Configuration Details

### `Containerfile` &mdash; the images being used

This project does not use direct references to online Hadoop and Spark images. Instead, it builds its own images using the `Containerfile` in the root directory. This allows for more control over the versions and configurations used, and "separates concecrns" by keeping `compose.yaml` unaware of the specific images being used.

The `Containerfile` relies on specific build _targets_ (as in multi-stage builds) to create the different types of images needed. The default build does not create a valid image; just one that errors and tells you to specify a target. The targets are:

- `hadoop_base`. This is the base image for others to inherit for. Based on `docker.io/apache/hadoop:3.4`.

- `hadoop_name_node`. This is the Hadoop NameNode image, which is the master node in a Hadoop cluster. It inherits from `hadoop_base`. Starting the name node is accomplished using the `start_name_node.sh` script, which includes logic for initializing the cluster.

- `hadoop_data_node`. This is the Hadoop DataNode image, which is the worker node in a Hadoop cluster. It inherits from `hadoop_base`. Starting the data node is accomplished using the `start_data_node.sh` script.

- `spark_base`. This is the base image for Spark, based on `docker.io/apache/spark:4.0.0`. It includes a skeleton of the Hadoop configuration files, which are needed for Spark to run on top of Hadoop.

- `spark_master`, `spark_worker`, `spark_history_server` and `spark_connect`. These images are based on `spark_base` and use the specific start scripts for their respective roles.

### `compose.yaml` &mdash; the container orchestration

The stack configured by this file includes:

- Network: `spark_sandbox`
  - This is a custom bridge network for the containers to communicate with each other, separate from the default container network. It is created automatically by `podman-compose` when the stack is started.
  - The subnet used is `172.77.0.0/16`, and containers are auto-assigned IP addresses. They reach each other using their service names (e.g., `hadoop-name1`, `spark-master`, etc.) as hostnames.
- Volumes: `hadoop-data1`, `hadoop-data2`, `hadoop-name1`
  - These are persistent volumes for the Hadoop NameNode and DataNodes, allowing them to retain their data across container restarts. These will not be deleted unless you explicitly remove them using `podman-compose down -v` or similar commands.
- Local mounts:
  - `./hadoop-config/` &rarr; `/opt/hadoop/etc/hadoop`: This is a local directory that contains the Hadoop configuration files. It is mounted into the containers _read-only_ and with the _`z` relabeling_ option (for proper SELinux context).
  - `./logs/` &rarr; `/opt/hadoop/logs`: This is a local directory that will contain the logs generated by the Hadoop services. It is mounted into the containers with read-write permissions and with the _`z` relabeling_ option (for proper SELinux context). It does not appear to be used by the current configuration (but is included for completeness).
- Services (and redundancy):
  - `hadoop-name1`: The Hadoop NameNode service, which is the master node in a Hadoop cluster. Uses the `hadoop_name_node` image.
  - `hadoop-data1` and `hadoop-data2`: Two Hadoop DataNode services, which are the worker nodes in a Hadoop cluster. They use the `hadoop_data_node` image. Two DataNodes are used to simulate a more realistic Hadoop cluster setup that includes redundancy. Note: a real Hadoop cluster would have at least three (and preferably more) DataNodes.
  - `spark-master`: The Spark master service, which is the master node in a Spark cluster. Uses the `spark_master` image.
  - `spark-worker1` and `spark-worker2`: Two Spark worker services, which are the worker nodes in a Spark cluster. They use the `spark_worker` image.
    - Two workers are used to simulate a more realistic Spark cluster setup that includes redundancy.
  - `spark-history-server`: The Spark history server service, which is used to view the history of completed Spark applications. Uses the `spark_history_server` image.
  - `spark-connect`: The Spark Connect service, which allows remote clients to connect to the Spark cluster. Uses the `spark_connect` image.

#### Exposed ports

| Port  | Service              | Description                               |
| ----- | -------------------- | ----------------------------------------- |
| 9870  | hadoop-name1         | HTTP port for the Hadoop NameNode web UI. |
| 9000  | hadoop-name1         | HDFS main port.                           |
| 9866  | hadoop-name1         | HDFS IPC port.                            |
| 9864  | hadoop-data1         | Web UI for the Hadoop DataNode 1.         |
| 9865  | hadoop-data2         | Web UI for the Hadoop DataNode 2.         |
| 8080  | spark-master         | Spark master web UI.                      |
| 7077  | spark-master         | Spark master port.                        |
| 8081  | spark-worker1        | Spark worker 1 web UI.                    |
| 8082  | spark-worker2        | Spark worker 2 web UI.                    |
| 18080 | spark-history-server | Spark history server web UI.              |
| 4040  | spark-connect        | Spark Connect web UI.                     |
| 15002 | spark-connect        | Spark Connect REST API.                   |

### `hadoop-config/` &mdash; the Hadoop configuration files

This directory contains the Hadoop configuration files needed for the Hadoop services to run. It is mounted into the containers as a read-only volume, so any changes made here will be reflected in the containers. The same files are used for all services, as typical for a Hadoop cluster.

### `pyproject.toml` and `scratch.py` &mdash; a sample PySpark application

This is a simple Python project which uses PySpark for connecting to this cluster. You do not need to actually use it for anything, if your code connects from elsewhere.

To set it up:

1. Install Python Poetry 2.1.3+. Follow the instructions at [Poetry's official documentation](https://python-poetry.org/docs/#installation).

2. Create a virtual environment and tell Poetry to use it:

   ```bash
   python3 -m venv .venv
   poetry env use .venv/bin/python
   ```

To use the packages installed by the virtual environment, you can do any of:

- Connect your virtual envirtonment to your IDE (e.g., PyCharm, VSCode, etc.), using the `.venv/bin/python` interpreter.
- Use `poetry shell` to activate the virtual environment in your terminal.
- Use `poetry run` to run commands within the virtual environment. For example, `poetry run python scratch.py`.
