# importing the module
import sqlite3
from datetime import datetime, timedelta
from pytz import timezone
import json

# connect withe the myTable database
connection = sqlite3.connect("attendance.db")

# cursor object to execute SQLite commands
crsr = connection.cursor()

def get_attendance(employee_code, date):
    """
    Accepts an employee code (e.g. EMP01)
    and a date (e.g. 2020-04-01)
    and reports whether the employee has attended that day and how long.
    """

    # Execute selection on the query for that provided employee_code and date ot get the employee
    crsr.execute("SELECT ActionTime FROM AttendanceActions JOIN Attendance ON AttendanceActions.AttendanceId = Attendance.id WHERE Attendance.employee = ? AND Attendance.day = ?", (employee_code, date))
    # Get the result of the output query
    employee = crsr.fetchall()
    # If the output is not zero then the employee has attended
    attended = True if len(employee) >= 1 else False

    # If the employee has attendedd
    if (attended):
        # Execute selection on the query for that provided employee_code and date to get the ActionTime
        crsr.execute("SELECT ActionTime FROM AttendanceActions JOIN Attendance ON AttendanceActions.AttendanceId = Attendance.id WHERE Attendance.employee = ? AND Attendance.day = ? AND AttendanceActions.Action = 'CheckIn'", (employee_code, date))
        # Get the result rows of the output query
        check_in = crsr.fetchall()
        # A list for the checkin times and dates
        check_in_list = []
        # Add the resulted rows from the queryset to the list
        for i in check_in:
            # Store the datetime stirng data in a datetime format for manipulating
            check_in_list.append(datetime.strptime(i[0], "%Y-%m-%d %I:%M %p"))

        # Execute selection on the query for that provided employee_code and date to get the ActionTime
        crsr.execute("SELECT ActionTime FROM AttendanceActions JOIN Attendance ON AttendanceActions.AttendanceId = Attendance.id WHERE Attendance.employee = ? AND Attendance.day = ? AND AttendanceActions.Action = 'CheckOut'", (employee_code, date))
        # Get the result rows of the output query
        check_out = crsr.fetchall()
        # A list for the checkin times and dates
        check_out_list = []
        # Add the resulted rows from the queryset to the list
        for i in check_out:
            # Store the datetime data in ISO format
            check_out_list.append(datetime.strptime(i[0], "%Y-%m-%d %I:%M %p"))

        # Handle when the employee chekin more than once in a day
        # Add opposite checkout or checkin time and date to get the time delta for that day
        if len(check_in_list) > len(check_out_list):
            n = len(check_in_list) - 1
            for i in range(n):
                check_out_list.append((check_in_list[0] + timedelta(days=1)).replace(hour=0, minute=0))
        elif len(check_out_list) > len(check_in_list):
            for i in range(len(check_out_list)):
                check_in_list.append((check_out_list[0] + timedelta(days=1)).replace(hour=0, minute=0))

        # Get the duration of attendance of that employee        
        hours = 0
        minutes = 0
        for i in range(len(check_in_list)):
            time_difference = check_out_list[i] - check_in_list[i]
            hours += time_difference.seconds // 3600
            minutes += (time_difference.seconds // 60) % 60

        return json.dumps({"attended": attended, "duration":  f"{hours}:{minutes}"}, indent=4)
    # If the employee has not attended    
    else:
        hours = 0
        minutes = 0
        # Return the data in JSON format
        return json.dumps({"attended": attended, "duration":  f"{hours}:{minutes}"}, indent=4)

# Test the function
print(get_attendance('EMP01', '2020-04-01'))
print(get_attendance('EMP01', '2020-04-02'))
print(get_attendance('EMP01', '2020-04-03'))
print(get_attendance('EMP02', '2020-04-01'))
print(get_attendance('EMP02', '2020-04-02'))
print(get_attendance('EMP02', '2020-04-03'))


def attendance_history(employee_code):
    """
    Accepts an employee code (e.g. EMP01) and returns the attendance history for that employee.
    An attendance history is a list of days, and within each day, a list of attendance actions. 
    """

    # Execute selection on the query for that provided employee_code to get the attended days
    crsr.execute("SELECT day FROM AttendanceActions JOIN Attendance ON AttendanceActions.AttendanceId = Attendance.id WHERE Attendance.employee = ?", (employee_code,))
    # Get the result of the output query
    days = crsr.fetchall()
    # days_list for storing the attended days dates
    days_list = []
    # Update the days_list to have the attended days dates
    for i in days:
        # Remove any duplications
        if (i[0] not in days_list):
            days_list.append(i[0])

    # Localize the datetime for convert the local datetime of actions time to utc timezone
    egypt_timezone = timezone('Egypt')
    utc_timezone = timezone('UTC')
    # days_dict for stroing the attended days and actions done in these days
    # As the day date is the key and the actions is the value in a list format for every action
    days_dict = {k:[] for k in days_list}
    # Get the days dates and filter the query using them
    for day in days_list:
        # Execute selection on the query for that provided employee_code and day date ot get the actions and action time for every attended day
        crsr.execute("SELECT Action, ActionTime FROM AttendanceActions JOIN Attendance ON AttendanceActions.AttendanceId = Attendance.id WHERE Attendance.employee = ? AND Attendance.day = ?", (employee_code, day))
        # Get the result of the output query
        actions = crsr.fetchall()
        # Update the days_dict to have the needed data
        for action in actions:
            # Store the datetime stirng data in a datetime format (object) for manipulating 
            action_time = datetime.strptime(action[1], "%Y-%m-%d %I:%M %p")
            # Localize the time
            loc_action_time = egypt_timezone.localize(action_time)
            # Convert it to UTC timezone
            action_time = loc_action_time.astimezone(utc_timezone)
            # convert it to ISO format
            action_time = action_time.isoformat()
            days_dict[f"{day}"].append({"action": action[0], "time": action_time})
    
    # attendance_history dictionary for storing data of the attended days and the employees actions in these days
    # As the days is the key and its data is a list of days and employees actions in these days
    attendance_history = {"days": []}
    # Update the attendance_history dictionary for having the needed data
    for day in days_dict:
        attendance_history["days"].append({'date': day, 'actions': days_dict[day]})
    
    # Return the data in JSON format
    return json.dumps(attendance_history, indent=4)

# Test the function
print(attendance_history('EMP01'))
print(attendance_history('EMP02'))
