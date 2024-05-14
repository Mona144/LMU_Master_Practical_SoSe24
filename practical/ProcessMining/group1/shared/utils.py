import csv
import os
import pandas as pd
import pm4py
import shutil
import uuid
from datetime import datetime
from pathlib import Path


TMP_LOGS_PATH = './tmp_logs'


def import_csv(file_path):
    event_log = pd.read_csv(file_path, sep=';')
    event_log = pm4py.format_dataframe(event_log, case_id='case_id', activity_key='activity', timestamp_key='timestamp')
    return event_log


def import_xes(file_path):
    event_log = pm4py.read_xes(file_path)
    return event_log


def event_log_to_csv(event_log):
    if os.path.exists(Path(TMP_LOGS_PATH)):
        shutil.rmtree(Path(TMP_LOGS_PATH))
    os.makedirs(TMP_LOGS_PATH, exist_ok=True)
    filename = f'{TMP_LOGS_PATH}/event_log_{uuid.uuid4()}.csv'
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(["case_id", "activity", "timestamp"])
        for i, activities in enumerate(event_log, start=1):
            for activity in activities:
                timestamp = datetime.now().isoformat()
                writer.writerow([i, activity, timestamp])
    return filename

