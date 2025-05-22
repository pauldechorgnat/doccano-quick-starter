from doccano_client import DoccanoClient

from doccano_client.models.data_upload import Task
from logger import logger
import os
import datetime
import json
import zipfile
from pathlib import Path
from custom import (
    get_unique_identifier_from_doccano_data,
    get_unique_identifier_from_raw_data,
    transform_raw_data_to_doccano_data,
    transform_doccano_data_to_annotated_data,
)


def create_doccano_client(
    username: str,
    password: str,
    base_url: str = "http://localhost:8000",
) -> DoccanoClient:
    doccano_client = DoccanoClient(
        base_url=base_url,
        # username=username,
        # password=password,
    )
    doccano_client.login(
        username=username,
        password=password,
    )
    return doccano_client


def read_jsonl(
    filename: str,
) -> list[dict]:
    with open(filename, "r", encoding="utf-8") as file:
        data = [json.loads(line) for line in file if len(line) > 2]
    return data


def write_jsonl(
    data: list[dict],
    filename: str,
):
    with open(filename, "w", encoding="utf-8") as file:
        file.write("\n".join(json.dumps(d) for d in data))


def extract_files_from_zipfile(
    filename: str | Path,
    delete_zipfile: bool = True,
):
    dirname = os.path.dirname(filename)
    with zipfile.ZipFile(filename, "r") as z:
        z.extractall(dirname)

    if delete_zipfile:
        os.remove(filename)


def get_doccano_project_id_by_name(
    doccano_client: DoccanoClient,
    project_name: str,
) -> int | None:
    projects = list(
        filter(
            lambda x: x.name == project_name,
            doccano_client.list_projects(),
        )
    )

    if len(projects) >= 1:
        return projects[0].id
    else:
        return None


def upload_new_data_to_doccano(
    new_data: list[dict],
    project_name: str,
    doccano_client: DoccanoClient,
):
    project_id = get_doccano_project_id_by_name(
        doccano_client=doccano_client,
        project_name=project_name,
    )

    if project_id is None:
        raise ValueError(f"Project `{project_name}` does not exist")

    temporary_folder_name = os.path.join(
        os.path.dirname(__file__),
        f"tmp_{format_date_into_filename(datetime.datetime.now())}",
    )
    logger.info(f"Creating temporary folder `{temporary_folder_name}`")
    os.mkdir(temporary_folder_name)
    try:
        logger.info(f"Downloading Doccano data into `{temporary_folder_name}`")
        zip_filename = doccano_client.download(
            project_id=project_id,
            format="JSONL",
            dir_name=temporary_folder_name,
        )

        logger.info(f"Extracting data from zip file `{zip_filename}`")
        extract_files_from_zipfile(
            filename=str(zip_filename),
            delete_zipfile=True,
        )

        old_data = set(
            get_unique_identifier_from_doccano_data(d=d)
            for f in os.listdir(temporary_folder_name)
            for d in read_jsonl(filename=os.path.join(temporary_folder_name, f))
        )

        logger.info("Comparing new data to old data")
        files_to_upload: list[str] = []

        for d in new_data:
            unique_identifier = get_unique_identifier_from_raw_data(d)
            if unique_identifier not in old_data:
                filename = os.path.join(temporary_folder_name, f"{unique_identifier}.jsonl")
                write_jsonl(filename=filename, data=[transform_raw_data_to_doccano_data(d=d)])
                files_to_upload.append(filename)

        logger.info(f"Uploading {len(files_to_upload)} to Doccano")
        doccano_client.upload(
            project_id=project_id,
            task=Task.SEQUENCE_LABELING,
            # task="SequenceLabeling",
            format="JSONL",
            file_paths=files_to_upload,
        )
    except Exception as exc:
        logger.error("Encountered an exception: ", exc)
    finally:
        logger.info(f"Removing temporary folder `{temporary_folder_name}`")
        for f in os.listdir(temporary_folder_name):
            os.remove(os.path.join(temporary_folder_name, f))
        os.rmdir(temporary_folder_name)


def format_date_into_filename(date: datetime.date) -> str:
    string = str(date)[:19]
    return string.replace(" ", "_").replace(":", "").replace("-", "")


def create_project(
    doccano_client: DoccanoClient,
    project_name: str,
    labels: list[dict],
    project_description: str = "",
):
    project_id = get_doccano_project_id_by_name(
        doccano_client=doccano_client,
        project_name=project_name,
    )

    if project_id is not None:
        logger.info(f"Project `{project_name}` already exists")
    else:
        logger.info(f"Creating `{project_name}` project")
        doccano_client.create_project(
            name=project_name,
            description=project_description,
            project_type="SequenceLabeling",
        )
        project_id = get_doccano_project_id_by_name(
            doccano_client=doccano_client,
            project_name=project_name,
        )
        if project_id is None:
            raise ValueError(f"Project `{project_name}` was not created")

        for label in labels:
            doccano_client.create_label_type(
                project_id=project_id,
                type=label["type"],
                text=label["name"],
                color=label["color"],
            )


def delete_doccano_project(
    doccano_client: DoccanoClient,
    project_name: str,
):
    project_id = get_doccano_project_id_by_name(
        doccano_client=doccano_client,
        project_name=project_name,
    )

    if project_id is None:
        raise ValueError(f"Project `{project_name}` does not exist")

    logger.info(f"Deleting `{project_name}` project")
    doccano_client.delete_project(project_id=project_id)


def download_data_from_doccano(
    doccano_client: DoccanoClient,
    project_name: str,
    annotated_data_folder: str,
):
    project_id = get_doccano_project_id_by_name(
        doccano_client=doccano_client,
        project_name=project_name,
    )

    if project_id is None:
        raise ValueError(f"Project `{project_name}` does not exist")

    temporary_folder_name = os.path.join(
        os.path.dirname(__file__),
        f"tmp_{format_date_into_filename(datetime.datetime.now())}",
    )
    logger.info(f"Creating temporary folder `{temporary_folder_name}`")

    os.mkdir(temporary_folder_name)
    logger.info(f"Downloading data into `{temporary_folder_name}`")
    try:
        zip_filename = doccano_client.download(
            project_id=project_id,
            format="JSONL",
            only_approved=True,
            dir_name=temporary_folder_name,
        )
        logger.info(f"Extracting data from zip file `{zip_filename}`")
        extract_files_from_zipfile(
            filename=zip_filename,
            delete_zipfile=True,
        )

        logger.info(f"Transforming data and saving it to `{annotated_data_folder}`")
        annotated_data = [
            transform_doccano_data_to_annotated_data(d=d)
            for f in os.listdir(temporary_folder_name)
            for d in read_jsonl(filename=os.path.join(temporary_folder_name, f))
        ]

        annotated_data_filename = os.path.join(
            annotated_data_folder,
            f"{format_date_into_filename(datetime.datetime.now())}_annotated_data.json",
        )
        with open(annotated_data_filename, "w") as file:
            json.dump(annotated_data, file)
    except Exception as exc:
        logger.error("Encountered an exception: ", exc)
    finally:
        logger.info(f"Removing temporary folder `{temporary_folder_name}`")
        for f in os.listdir(temporary_folder_name):
            os.remove(os.path.join(temporary_folder_name, f))
        os.rmdir(temporary_folder_name)
