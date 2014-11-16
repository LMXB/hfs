# Script automates hysplit daily trajectory computations up to 8 weeks backwards.
# Trajectory model runs by executing binary "hyts_std.exe". Before execution,
# additional configuration files have to be prepared in the current working
# directory.
#
# Global configurations are stored in SETUP.CFG. ASCDATA.CFG holds default
# constant values for land use and roughness length. CONFIG file specifies
# the run and especially paths to to meteo GDAS files.
#
# Runs are defined in the file "runs.csv" in a comma-separated values format.
# Values are in the folowing order:
# OUTPUT FOLDER, LATITUDE, LONGTITUDE, HEIGHT, YEAR, MONTH, DAY, BACKWARD TIME IN HOURS
#
# Dusan Lago <dusan.lago at gmail.com>
# Tested with Python 2.7.6
# 2014-10-19

"""Modules"""
import csv
import os
import subprocess
from subprocess import Popen, PIPE
from datetime import date, timedelta
from timeit import time
from sets import Set
import calendar
import math


"""Constants"""

hysplit_bin = 'C:\\hysplit4\\exec\\hyts_std.exe'
meteo_dir = 'E:\\meteo\\'
output_dir = 'E:\\meteo\\'
csv_source = 'sample_run.csv'
# Execution start time stamp
startTime = time.time()
# Load runs from csv file
csv_input = csv.reader(open(csv_source, 'r'))

# ASCDATA.CFG
ASCDATA = """-90.0   -180.0  lat/lon of lower left corner
1.0     1.0     lat/lon spacing in degrees
180     360     lat/lon number of data points
2               default land use category
0.2             default roughness length (m)
'C:/hysplit4/bdyfiles/'  directory of files
"""

# SETUP.CFG
SETUP = """&SETUP\ntratio = 0.75,\nmgmin = 15,\nkhmax = 9999,\nkmixd = 0,
kmsl = 0,\nnstr = 0,\nmhrs = 9999,\nnver = 0,\ntout = 60,\ntm_tpot = 0,
tm_tamb = 0,\ntm_rain = 1,\ntm_mixd = 1,\ntm_relh = 0,\ntm_sphu = 0,
ntm_mixr = 0,\ntm_dswf = 0,\ntm_terr = 0,\ndxf = 1.0,\ndyf = 1.0,
dzf = 0.01,\n/
"""


"""Additional functions"""

# Calculate the week number of month
# Taken from http://stackoverflow.com/a/7029955
def week_of_month(tgtdate):

    days_this_month = calendar.mdays[tgtdate.month]
    for i in range(1, days_this_month):
        d = date(tgtdate.year, tgtdate.month, i)
        if d.day - d.weekday() > 0:
            startdate = d
            break
    # now we can use the modulo 7 approach
    return (tgtdate - startdate).days //7 + 1

# Create ASCDATA.CFG
def createASCDATA():
    ascdataFile = open('ASCDATA.CFG', 'w')
    ascdataFile.write(ASCDATA)
    ascdataFile.close()

# Create SETUP.CFG
def createSETUP():
    setupFile = open('SETUP.CFG', 'w')
    setupFile.write(SETUP)
    setupFile.close()


"""Main"""
# Main loop. Cycling throught the lines in csv file and for each
# day within period runs model in specified hours.
for line in csv_input:

    # Load values
    working_dir = line[0]
    lat = line[1]
    lon = line[2]
    height = line[3]
    start_date = date(int(line[4]), int(line[5]), int(line[6]))
    end_date = date(int(line[7]), int(line[8]), int(line[9]))
    runtime = int(line[10])
    runtime_weeks = math.ceil(runtime/(24.0*7))
    hours = line[11].split()
    top_model = line[12]
    
    # Make dir for current run
    if not os.path.exists(working_dir):
        os.mkdir(working_dir)

    os.chdir(working_dir)

    print(working_dir)

    # Create log file
    log = open('run.log', 'w')

    # ASCDATA.CFG
    createASCDATA()

    # SETUP.CFG
    createSETUP()

    while start_date <= end_date:
        for hour in hours:

            # Create control file, based on hysplit manual
            control = open('CONTROL', 'w')
            control.write(start_date.strftime('%y %m %d ') + hour + '\n')
            control.write('1\n')
            control.write(lat + ' ' + lon + ' ' + height + '\n')
            control.write(str(runtime) + '\n')
            control.write('0\n') # vertical motion
            control.write(top_model + '\n')
            control.write(str(runtime_weeks) + '\n')

            # Add sufficient number of meteo files
            if runtime_weeks > 0:
                meteo_date_end = start_date + timedelta(weeks=runtime_weeks)
                meteo_date_start = start_date
            else:
                meteo_date_start = start_date - timedelta(weeks=abs(runtime_weeks))
                meteo_date_end = start_date

            # Set of all meteo files is created
            meteo_files = Set()

            while meteo_date_start <= meteo_date_end:
                meteo_files.add('gdas1.' + meteo_date_start.strftime('%b%y').lower() \
                    + '.w' + str(week_of_month(meteo_date_start)))
                meteo_date_start = meteo_date_start + timedelta(days=1)

            for meteo_file in meteo_files:
                control.write(meteo_dir + '\n')
                control.write(meteo_file + '\n')

            # Output location
            control.write(os.getcwd() + '\\\n')
            control.write(start_date.strftime('%y%m%d') + hour)
            control.close()

            # Run model and log it's output
            run = Popen(hysplit_bin, stdout=PIPE, stderr=PIPE)
            run_out = run.communicate()
            log.write(run_out[0])
            log.write(run_out[1])

        start_date += timedelta(days=1)
    os.chdir('../')
    log.close()

print "Script time execution was:\n%d seconds or %d minutes" % (time.time() \
    - startTime, (time.time() - startTime)/60)
raw_input()