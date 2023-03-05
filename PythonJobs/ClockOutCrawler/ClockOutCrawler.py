import re
import pandas as pd
import pdfplumber
import pyodbc
import uuid
import os
import time as tm
from datetime import datetime, time, timedelta
from pandasql import sqldf
import sqlalchemy
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

report_start_date = "02/15/2023"
report_end_date = "03/03/2023"
username = ""
password = ""


login_url = "https://cfahome.okta.com/login/login.htm"
scrape_url = "https://backoffice.cfahome.com/tp/tpActualVsScheduledVarianceFilterAction.do"


profile = webdriver.FirefoxProfile()
profile.set_preference("browser.download.folderList", 2)
profile.set_preference("browser.download.dir", os.getcwd())
profile.set_preference("browser.download.manager.alertOnEXEOpen", False)
profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/msword, application/csv, "
                                                                 "application/ris, text/csv, image/png, "
                                                                 "application/pdf, text/html, text/plain, "
                                                                 "application/zip, application/x-zip, "
                                                                 "application/x-zip-compressed, application/download, "
                                                                 "application/octet-stream")
profile.set_preference("browser.download.manager.showWhenStarting", False)
profile.set_preference("browser.download.manager.focusWhenStarting", False)
profile.set_preference("browser.download.useDownloadDir", True)
profile.set_preference("browser.helperApps.alwaysAsk.force", False)
profile.set_preference("browser.download.manager.alertOnEXEOpen", False)
profile.set_preference("browser.download.manager.closeWhenDone", True)
profile.set_preference("browser.download.manager.showAlertOnComplete", False)
profile.set_preference("browser.download.manager.useWindow", False)
profile.set_preference("services.sync.prefs.sync.browser.download.manager.showWhenStarting", False)
profile.set_preference("pdfjs.disabled", True)

driver = webdriver.Firefox(profile)
driver.get(login_url)



## Login section
print("Logging in...")

# Username
username_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
username_field.send_keys(username)
next_button = driver.find_element(By.ID, "okta-signin-submit")
next_button.click()

# Password
password_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "password")))
password_field.send_keys(password)
password_field.send_keys(Keys.RETURN)

# Wait for auth
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "dashboard-my-apps-title")))


## Scrape Section
print("Crawling...")
driver.get(scrape_url)

# Report fields
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "reportStartDate")))
driver.execute_script(f"document.getElementById('reportStartDate').value = \"{report_start_date}\";")
driver.execute_script(f"document.getElementById('reportEndDate').value = \"{report_end_date}\";")

# View report button
button = driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/table/tbody/tr/td[2]/div[2]/table/tbody/tr/td/div/form/table/tbody/tr[2]/td/table[3]/tbody/tr/td/input")
button.click()
driver.close()


print("Retrieving report...")
while not os.path.exists(os.path.join(os.getcwd(), "tpActualVsScheduledVarianceAction.pdf")):
    tm.sleep(1)
tm.sleep(2)


## Parse report section
print("Parsing report...")

report_content = ""
with pdfplumber.open("tpActualVsScheduledVarianceAction.pdf") as pdf:
    for page in pdf.pages:
        report_content += "\n" + page.extract_text(layout=True, x_density=6)

pattern = r"(Actual|Vs.|Punch|Report|Orland|Park|FSU|Clock-In|Clock-Out|Employee" \
          r"Name|Date|Actual|Scheduled|Clock-In/Out|Clock-In/Out|Variance|Employee Name|/Out|Working)"
clean_report = re.sub(pattern, "|", report_content)
clean_report = "|".join([s for s in re.split(r"\n+", clean_report) if s])
cleaner_report = re.sub(r"\|+", "\n", clean_report)

lines = cleaner_report.splitlines()
report_date_range = ""
for line in lines:
    if line.strip() != "":
        report_date_range = line
        break
lines.remove(report_date_range)
cleanerer_report = "\n".join(lines)

split_pattern = r"(?=Total Time:.*\n)"
split_report = re.split(split_pattern, cleanerer_report)
split_report = list(filter(None, split_report))
split_report = split_report[:-2]

column_names = ["Employee Name", "Date", "FromTimeActual", "ThruTimeActual", "FromTimeScheduled", "ThruTimeScheduled",
                "ClockInVarianceOverage", "ClockInVarianceShortage", "ClockOutVarianceOverage", "ClockOutVarianceShortage",
                "ClockInOutVarianceOverage", "ClockInOutVarianceShortage"]
df = pd.DataFrame(columns=column_names)
now = datetime.now()

for employee in split_report:
    rows = employee.split("\n")
    filtered_rows = [s for s in rows if s.strip() and s.strip() != "Time" and not any(substring in s for substring in ['Total', 'Overage', 'Shortage', 'Page'])]
    name = filtered_rows[0].strip()

    chop_width = 1
    for i in range(1, len(filtered_rows)):
        if "Time" in filtered_rows[i]:
            chop_width = i
            break

    filtered_rows = filtered_rows[chop_width:]
    filtered_rows[0] = filtered_rows[0].replace("Time ", "                   ")
    filtered_rows = [s.rstrip(" ")[20:].replace(" AM", "AM").replace(" PM", "PM").rstrip() for s in filtered_rows]

    for i in range(len(filtered_rows)):
        filtered_rows[i] = filtered_rows[i].replace("      ", " -- ", 1) if i % 2 == 0 \
            else filtered_rows[i].replace("                ", " -- ")

    filtered_rows = [re.sub(r'\s{2,}', ' ', s.replace("----", "-- --")) for s in filtered_rows]
    filtered_rows = [s for s in filtered_rows if s != '']

    for i in range(0, len(filtered_rows), 2):
        raw_row_1 = [s for s in filtered_rows[i].split(" ") if s != ""]
        raw_row_2 = filtered_rows[i + 1].split(" ") if i < len(filtered_rows) - 1 else []
        raw_row_2 = [elem for elem in raw_row_2 if elem != '']
        raw_row_2 = raw_row_2 + [None] * (2 - len(raw_row_2))

        civo = (raw_row_1[3] if raw_row_1[3] != "--" and raw_row_1[3] != None and raw_row_1[3][0] != "(" else "").split(":")
        civs = (raw_row_1[3].replace("(", "").replace(")", "") if raw_row_1[3] != "--" and raw_row_1[3] != None and raw_row_1[3][0] == "(" else "").split(":")
        covo = (raw_row_1[4] if raw_row_1[4] != "--" and raw_row_1[4] != None and raw_row_1[4][0] != "(" else "").split(":")
        covs = (raw_row_1[4].replace("(", "").replace(")", "") if raw_row_1[4] != "--" and raw_row_1[4] != None and raw_row_1[4][0] == "(" else "").split(":")

        row = pd.DataFrame({
            "ReportRunDate": now,
            "EmployeeName": [name],
            "ShiftDate": [datetime.strptime(raw_row_1[0], '%m/%d/%Y')],
            "FromTimeActual": [datetime.strptime(raw_row_1[1], '%I:%M%p').time() if raw_row_1[1] != "--" and raw_row_1[1] != None else None],
            "ThruTimeActual": [datetime.strptime(raw_row_2[0], '%I:%M%p').time() if raw_row_2[0] != "--" and raw_row_2[0] != None else None],
            "FromTimeScheduled": [datetime.strptime(raw_row_1[2], '%I:%M%p').time() if raw_row_1[2] != "--" and raw_row_1[2] != None else None],
            "ThruTimeScheduled": [datetime.strptime(raw_row_2[1], '%I:%M%p').time() if raw_row_2[1] != "--" and raw_row_2[1] != None else None],
            "ClockInVarianceOverage": [int(civo[0])*60 + int(civo[1]) if len(civo) != 0 and civo[0] != "" else None],
            "ClockInVarianceShortage": [int(civs[0])*60 + int(civs[1]) if len(civs) != 0 and civs[0] != "" else None],
            "ClockOutVarianceOverage": [int(covo[0])*60 + int(covo[1]) if len(covo) != 0 and covo[0] != "" else None],
            "ClockOutVarianceShortage": [int(covs[0])*60 + int(covs[1]) if len(covs) != 0 and covs[0] != "" else None],
            "ClockInOutVarianceOverage": ['{:.2f}'.format(float(raw_row_1[-2])) if raw_row_1[-2] != "--" and raw_row_1[-2] != None else None],
            "ClockInOutVarianceShortage": ['{:.2f}'.format(float(raw_row_1[-1].replace("(", "").replace(")", "").replace("$", ""))) if raw_row_1[-1] != "--" and raw_row_1[-1] != None else None]
        })

        df = pd.concat([df, row], ignore_index=True)


## Connect to SQL server

cnxn = pyodbc.connect("Driver={SQL Server Native Client 11.0};"
                      "Server=(LocalDb)\\MSSQLLocalDB;"
                      "Database=CFA-Orland;"
                      "Trusted_Connection=yes;")
cursor = cnxn.cursor()
cursor.fast_executemany = True
for index, row in df.iterrows():
    cursor.execute(
        "INSERT INTO ClockOutReportRuns (Id, ReportRunDate, EmployeeName, ShiftDate, FromTimeActual, ThruTimeActual,\
        FromTimeScheduled, ThruTimeScheduled, ClockInVarianceOverage, ClockInVarianceShortage, ClockOutVarianceOverage,\
        ClockOutVarianceShortage, ClockInOutVarianceOverage, ClockInOutVarianceShortage) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        str(uuid.uuid4()), row.ReportRunDate, row.EmployeeName, row.ShiftDate, row.FromTimeActual, row.ThruTimeActual,
        row.FromTimeScheduled, row.ThruTimeScheduled, row.ClockInVarianceOverage, row.ClockInVarianceShortage,
        row.ClockOutVarianceOverage, row.ClockOutVarianceShortage, row.ClockInOutVarianceOverage,
        row.ClockInOutVarianceShortage
    )
cnxn.commit()
cursor.close()
os.remove("tpActualVsScheduledVarianceAction.pdf")

print("Done")