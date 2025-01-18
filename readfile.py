
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



def process_file(file_path = "",method = ""):
    # Ensure the file exists
    success = True
    if not os.path.exists(file_path):
        return {"status": "error", "message": "File not found"}
    if method == "pdf":
        try:
            result = retrieve_pdf(file_path)
        except :
            success = False
            result =  "Error in making time table"
    else:
        try:
            result = retrieve_excel(file_path)
        except :
            success = False
            result = "Error in making time table"
        
    return {
        "message": result,
        "success": success
    }

def retrieve_pdf(file_path):
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


def retrieve_excel(file_path):

    # calculate all sheet available
    
    # xl = pd.ExcelFile('file.xlsx')
    # res = len(xl.sheet_names)
    
    
    dataframe1 = pd.read_excel(file_path, index_col=0, header=None)
    timetable = dataframe1.iloc[4:]

    item_list = findExcelSub(timetable)
    week = getWeek(dataframe1)
    timeline = findTimeline(dataframe1)

    for item in item_list:
        if isinstance(item["timeStartRef"], int):
            time_index = item["timeStartRef"]-1  # Adjusting for index (time list starts from 0)
            item["timeStartRef"] = timeline[time_index]
        
    
    return {"timetable":item_list, "week":week}

    
def getWeek(dataframe1):
    header = dataframe1.index[0]
    week = header.split(" ")
    return week[1]

def findExcelSub(dataframe1):
    matched_subjects = []
    column = 0
    for col in dataframe1.columns:
        column += 1
        row = 0
        # if pd.isna(monday[col].tolist()[0]):
        for col1 in dataframe1[col]:
            row +=1
            if not pd.isna(col1):
                clean_text = col1.replace('"','')
                clean_text = clean_text.replace('\n',' ')

                if row <= 2 and row > 0:
                    day = 1
                elif row <= 4 and row > 2:
                    day = 2
                elif row <= 6 and row > 4:
                    day = 3
                elif row <= 8 and row > 6:
                    day = 4
                else:
                    day = 5

                if re.match(r"\b[A-Z]{2,3}\s?\d{3,5}\b", str(clean_text)):
                    if re.match(r"\bMPU\b", str(clean_text)):
                        clean_text = clean_text.replace(" ","")

                    group_text = clean_text.split(" ")
                    if len(group_text) > 1:
                        matched_subjects.append({"timeStartRef":column,"subjectRef": group_text[0],"hallRef": group_text[1], "dayRef":str(day), "durationRef":"1.5"})
                    else:
                        matched_subjects.append({"timeStartRef":column,"subjectRef": group_text[0], "hallRef":"", "dayRef":str(day), "durationRef":"1.5"})


    return matched_subjects

def findTimeline(dataframe1):
    timeList = dataframe1.iloc[3]
    time = []
    for col in timeList:
        fulltime_list = col.split(" ")[0]
        formatted_time = fulltime_list[:2] + "." + fulltime_list[2:]
        time.append(formatted_time)
    return time


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
        
    return process_file(file_location,"pdf")

@app.post("/uploadexcel/")
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
    
    return process_file(file_location,"excel")

