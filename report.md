## Running airflow in docker

### 1 docker compose

docker compose is basically a multi container tool, allow us to run multi-container app, which is exactly the case of airflow. Airflow has at least 3 components web server, scheduler, meta database, etc.

Then we download all the docker compose file describing all the services needed by airflow.

```shell
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.10.5/docker-compose.yaml'
```

Inside this docker compose yaml file:
below the services are all components, service is the only required element

### 1.5

The docker compose is based on airflow image, so no need to create any env anywhere outside.

If extra libraries needed, check docs for extending the current docker image and change corresponding part of docker-compose.yaml.

Check the current environments:

```bash
docker exec -it amazon_books_data_pipeline-airflow-webserver-1 bash
pip list
```

### 2 set-ups

This is to make sure that user and group permissions are the same between those folders from your host and the folders in you containers.

This issue primarily occurs on Linux systems, where file and directory access permissions are tied to user IDs (UIDs) and group IDs (GIDs). By default, processes within Docker containers run as the root user (UID=0). If the root user inside the container creates files (e.g., logs or DAG files), these files will be owned by root on the host machine as well. As a result, normal users on the local machine may not have the permissions to access or modify these files. This creates a synchronization issue, since development and file management happen on the local machine. The container is just a user space.

If we don't solve it then basically we have to sudo all the time. So first step in set-ups is to set the <AIRFLOW_UID> of the container so that it matches the local user.

For windows, we don't have this techniqally but
warning that <AIRFLOW_UID> is not set might occur. Then we just set it anyway

```shell
mkdir -p ./dags ./logs ./plugins ./config
echo "AIRFLOW_UID=50000" > .env

docker compose up airflow-init

docker compose up
```

and then we create a second terminal to check everything correct

```shell
docker compose ps
```

### 3 connection

When creating connection to postgres from both pgadmin and airflow, just simply use postgres -- the service name of postgres as hostname.

Better not use the exact IP address of postgres service, it change all the time and connection may fail next time.
