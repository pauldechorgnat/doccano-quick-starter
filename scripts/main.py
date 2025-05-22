from argparse import ArgumentParser
from config import doccano_client, PROJECT_NAME
from utils import (
    create_project,
    upload_new_data_to_doccano,
    download_data_from_doccano,
    delete_doccano_project,
)
import json


argument_parser = ArgumentParser(
    description="Main entrypoint to interact with Doccano",
)

argument_parser.add_argument(
    "action",
    choices=[
        "init-project",
        "upload-data",
        "download-data",
        "delete-project",
    ],
    help="Action to perform",
)
argument_parser.add_argument(
    "--label-settings-file",
    default="./settings/label-settings.json",
    help="Path to file containing label description",
)
argument_parser.add_argument(
    "--project-description",
    default="My awesome project",
    help="Description of the project",
)
argument_parser.add_argument(
    "--input-data-file",
    default="./raw-data/raw-data.json",
    help="Path to file containing data to upload in Doccano",
)
argument_parser.add_argument(
    "--output-data-folder",
    default="./annotated-data",
    help="Path to folder containing annotated data",
)
argument_parser.add_argument(
    "--project-name", default=None, help="Name of the project if not provided will use env variables"
)


arguments = argument_parser.parse_args()

action = arguments.action

if arguments.project_name is not None:
    project_name = arguments.project_name
else:
    project_name = PROJECT_NAME

if action == "init-project":
    project_description = arguments.project_description
    label_settings_file = arguments.label_settings_file

    with open(label_settings_file, "r", encoding="utf-8") as file:
        labels = json.load(file)

    create_project(
        doccano_client=doccano_client,
        project_name=project_name,
        project_description=project_description,
        labels=labels,
    )

elif action == "upload-data":
    input_data_file = arguments.input_data_file
    with open(input_data_file, "r", encoding="utf-8") as file:
        new_data = json.load(file)

    upload_new_data_to_doccano(
        new_data=new_data,
        project_name=project_name,
        doccano_client=doccano_client,
    )
elif action == "download-data":
    output_data_folder = arguments.output_data_folder
    download_data_from_doccano(
        doccano_client=doccano_client,
        project_name=project_name,
        annotated_data_folder=output_data_folder,
    )

elif action == "delete-project":
    delete_doccano_project(
        doccano_client=doccano_client,
        project_name=project_name,
    )
