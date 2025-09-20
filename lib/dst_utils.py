"""
Daylight Saving Time (DST) Utilities
Handles automatic DST calculation for US timezones
"""

import time
import machine

def is_dst_active(year, month, day, timezone_hours):
    """
    Check if DST is active for a given date in US timezones
    DST in US: Second Sunday in March to First Sunday in November
    """
    if timezone_hours >= 0:
        # DST only applies to negative (western) timezones
        return False
    
    # DST period: March to November
    if month < 3 or month > 11:
        return False
    if month > 3 and month < 11:
        return True
        
    # March: DST starts second Sunday
    if month == 3:
        # Find second Sunday
        first_day_weekday = day_of_week(year, 3, 1)
        first_sunday = 7 - first_day_weekday if first_day_weekday != 6 else 7
        second_sunday = first_sunday + 7
        return day >= second_sunday
        
    # November: DST ends first Sunday  
    if month == 11:
        # Find first Sunday
        first_day_weekday = day_of_week(year, 11, 1)
        first_sunday = 7 - first_day_weekday if first_day_weekday != 6 else 7
        return day < first_sunday
        
    return False

def day_of_week(year, month, day):
    """
    Calculate day of week (0=Sunday, 1=Monday, ..., 6=Saturday)
    Using Zeller's congruence algorithm
    """
    if month < 3:
        month += 12
        year -= 1
        
    k = year % 100
    j = year // 100
    
    h = (day + ((13 * (month + 1)) // 5) + k + (k // 4) + (j // 4) - 2 * j) % 7
    
    # Convert to Sunday=0 format
    return (h + 5) % 7

def get_current_timezone_offset(base_timezone_hours, dst_enabled=True):
    """
    Get current timezone offset accounting for DST
    base_timezone_hours: Standard time offset (e.g., -5 for EST)
    dst_enabled: Whether to apply DST
    Returns: Current timezone offset in hours
    """
    if not dst_enabled:
        return base_timezone_hours
        
    try:
        # Get current date from RTC
        rtc = machine.RTC()
        dt = rtc.datetime()
        year, month, day = dt[0], dt[1], dt[2]
        
        if is_dst_active(year, month, day, base_timezone_hours):
            return base_timezone_hours + 1  # Add 1 hour for DST
        else:
            return base_timezone_hours
            
    except:
        # Fallback to standard time if RTC fails
        return base_timezone_hours

def get_dst_transition_dates(year):
    """
    Get DST transition dates for a given year
    Returns: (start_date, end_date) as (month, day) tuples
    """
    # Second Sunday in March
    first_day_march = day_of_week(year, 3, 1)
    first_sunday_march = 7 - first_day_march if first_day_march != 6 else 7
    dst_start = first_sunday_march + 7
    
    # First Sunday in November
    first_day_nov = day_of_week(year, 11, 1)
    first_sunday_nov = 7 - first_day_nov if first_day_nov != 6 else 7
    dst_end = first_sunday_nov
    
    return (3, dst_start), (11, dst_end)

def format_timezone_string(base_timezone_hours, dst_enabled=True):
    """
    Format timezone string with DST indication
    """
    current_offset = get_current_timezone_offset(base_timezone_hours, dst_enabled)
    
    if current_offset == base_timezone_hours:
        # Standard time
        if base_timezone_hours == -5:
            return "EST"
        elif base_timezone_hours == -6:
            return "CST"
        elif base_timezone_hours == -7:
            return "MST"
        elif base_timezone_hours == -8:
            return "PST"
        else:
            return f"UTC{current_offset:+d}"
    else:
        # Daylight time
        if base_timezone_hours == -5:
            return "EDT"
        elif base_timezone_hours == -6:
            return "CDT"
        elif base_timezone_hours == -7:
            return "MDT"
        elif base_timezone_hours == -8:
            return "PDT"
        else:
            return f"UTC{current_offset:+d}"

def is_dst_transition_day(year, month, day):
    """
    Check if given date is a DST transition day
    Returns: "start", "end", or None
    """
    start_date, end_date = get_dst_transition_dates(year)
    
    if month == start_date[0] and day == start_date[1]:
        return "start"
    elif month == end_date[0] and day == end_date[1]:
        return "end"
    else:
        return None

# Test the DST calculation
if __name__ == "__main__":
    # Test dates
    test_dates = [
        (2024, 3, 10),  # Second Sunday in March 2024 - DST starts
        (2024, 7, 15),  # Summer - DST active
        (2024, 11, 3),  # First Sunday in November 2024 - DST ends
        (2024, 12, 25), # Winter - DST inactive
        (2025, 3, 9),   # Second Sunday in March 2025 - DST starts
        (2025, 11, 2),  # First Sunday in November 2025 - DST ends
    ]
    
    for year, month, day in test_dates:
        dst_active = is_dst_active(year, month, day, -5)
        current_offset = get_current_timezone_offset(-5, True)
        tz_string = format_timezone_string(-5, True)
        print(f"{year}-{month:02d}-{day:02d}: DST={dst_active}, Offset={current_offset}, TZ={tz_string}")