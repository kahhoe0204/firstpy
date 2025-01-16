
import tabula
import pandas as pd
import glob
import re
import sys
import os
import json
import requests
import shutil

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:3000",  # Allow front-end running on port 3000 (example)
    "http://127.0.0.1:8000",
    "http://localhost:5173",
    "https://timetable.kahhoechoo",
    "*"
    # You can add more origins or use "*" for any origin
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow these origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods like GET, POST, etc.
    allow_headers=["*"],  # Allow all headers
)

# Find all matching patterns in the subject string
pattern = r'([A-Z]{3,4}\d{3,4}(?:[A-Z]{3,4}\d{3,4})*)'

# file_path = "uploaded_files/Semester 3 2025 Timetable v4.pdf"
area = [151.00, 91.00, 627.90, 500.94]

timetablearea = [150.6600030899048,132.80400272369386,161.82000331878663,504.0600103378296]

mondayarea = [152.89200313568116,133.54800273895265,261.5160053634644,504.0600103378296]
tuesdayarea = [261.10599075651515,133.54800273895265,368.8502265428975,504.0600103378296]
wednesdayarea = [367.9813214155879,133.54800273895265,476.59446232927974,504.0600103378296]
thursdayarea = [476.59446232927974,133.54800273895265,561.7471648056141,504.0600103378296]
fridayarea = [562.6160699329237,133.54800273895265,626.0461442265197,504.0600103378296]

timeline = []

pd.set_option('display.max_rows', None)  # Display all rows
pd.set_option('display.max_columns', None)  # Display all columns
pd.set_option('display.width', None)  # Avoid line wrapping
pd.set_option('display.max_colwidth', None)  # Display full content in each cell



def process_file(file_path = ""):
    # Ensure the file exists
    if not os.path.exists(file_path):
        return {"status": "error", "message": "File not found"}
    
    result = retreive_pdf(file_path)
    return result

def retreive_pdf(file_path):
# if __name__ == "__main__":
#     # Get the file path from the command-line arguments
#     if len(sys.argv) < 2:
#         result = {"status": "error", "message": "No file path provided"}
#     else:
#         file_path = sys.argv[1]
#         result = process_file(file_path)
    
#     # Output the result as JSON
#     print(json.dumps(result))

    # tabula.convert_into(file_path, "monday.csv",area=mondayarea,guess=False, output_format='csv', stream=True, pages="all")
    # tabula.convert_into(file_path, "time.csv",area=timetablearea,guess=False, output_format='csv', stream=True, pages="all")
    # return file_path

    time = tabula.read_pdf(file_path,area=timetablearea,guess=False, stream=True, pages="all")[0]

    monday = tabula.read_pdf(file_path,area=mondayarea,guess=False, stream=True, pages="all")[0]
    tuesday = tabula.read_pdf(file_path,area=tuesdayarea,guess=False, stream=True, pages="all")[0]
    wednesday = tabula.read_pdf(file_path,area=wednesdayarea,guess=False, stream=True, pages="all")[0]
    thursday = tabula.read_pdf(file_path,area=thursdayarea,guess=False, stream=True, pages="all")[0]
    friday = tabula.read_pdf(file_path,area=fridayarea,guess=False, stream=True, pages="all")[0]


    for col in time.columns:
        if pd.isna(time[col].tolist()[0]):
            timeline.append(col)
        else :
            timeline.append(str(time[col].tolist()[0]))

    # Iterate through the objectlist and apply mapping
    monday_objects = [map_to_time(obj) for obj in findSubject(monday)]
    tuesday_objects = [map_to_time(obj) for obj in findSubject(tuesday)]
    wednesday_objects = [map_to_time(obj) for obj in findSubject(wednesday)]
    thursday_objects = [map_to_time(obj) for obj in findSubject(thursday)]
    friday_objects = [map_to_time(obj) for obj in findSubject(friday)]

    # Print mapped result
    time_schedule = {"1":monday_objects,"2":tuesday_objects,"3":wednesday_objects,"4":thursday_objects,"5":friday_objects}
    return time_schedule



def findSubject(df):
    matched_subjects = []
    column = 0
    for col in df.columns:
        column += 1
        # if pd.isna(monday[col].tolist()[0]):
        for col1 in df[col]:
            if not pd.isna(col1):
                if re.match(pattern, str(col1)):
                    # print(col1)
                    matched_subjects.append({column: col1})

    return matched_subjects

# print(findSubject(wednesday))
# print(timeline)


# Mapping function
def map_to_time(list):
    mapped = {}
    for item in list:
        if isinstance(item, int):
            time_index = item - 1  # Adjusting for index (time list starts from 0)
            mapped[timeline[time_index]] = list[item]
        else:
            mapped[item] = item
    return mapped





@app.post("/uploadpdf/")
async def upload_file(file: UploadFile):

    save_directory = "uploaded_files"
    os.makedirs(save_directory, exist_ok=True)  # Create the directory if it doesn't exist

    # Construct the full path to save the file
    file_path = os.path.join(save_directory, file.filename)

    # Save the file to the specified path
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
        file_location = save_directory +"/"+ file.filename
        # file_location = "uploaded_files/Semester 3 2025 Timetable v4.pdf"
        
        result = process_file(file_location)
    
    return {
        "message": result,
        "success": True
    }



