from datetime import datetime, timedelta
import calendar
import pandas as pd
import numpy as np

def process_attendance_data(df,year=None, month=None, is_holiday=[]):


    _, max_day = calendar.monthrange(year, month)
    days = list(range(1, max_day + 1))

    df['attendance_date'] = df['attendance_date'].astype('str')
    df['status_str'] = df['shift_type'] + '，' + df['attendance_status'] + '，' + df['overtime_hours'].astype('str')
    df['day'] = df['attendance_date'].str[-2:]

    pivot = df.pivot_table(index='employee_id', columns='day', values='status_str', aggfunc='first', fill_value='')

    # 对 pivot 表做补全处理
    for day in [f"{i:02d}" for i in days]:
        if day not in pivot.columns:
            pivot[day] = ''  # 补空字符串

    weekends = {
        'Saturday': [],
        'Sunday': [],
        'is_holiday': is_holiday
    }


    for day in range(1, max_day + 1):
        date = datetime(year, month, day)
        weekday = date.weekday() 
        if weekday == 5 and f"{day:02d}" not in weekends['is_holiday']:
            weekends['Saturday'].append(f"{day:02d}")
        elif weekday == 6 and f"{day:02d}" not in weekends['is_holiday']:
            weekends['Sunday'].append(f"{day:02d}")

    # 工作日加班
    pivot['延时加班'] = df[~df['day'].isin(weekends['Saturday'] + weekends['Sunday'] + weekends['is_holiday'])].groupby('employee_id')['overtime_hours'].sum()
    # 周六,周日，节假日加班
    pivot['周六加班'] = df[df['day'].isin(weekends['Saturday'])].groupby('employee_id')['overtime_hours'].sum()
    pivot['周日加班'] = df[df['day'].isin(weekends['Sunday'])].groupby('employee_id')['overtime_hours'].sum()
    pivot['节假日加班'] = df[df['day'].isin(weekends['is_holiday'])].groupby('employee_id')['overtime_hours'].sum()

    status_statistics = df.groupby(['employee_id', 'attendance_status']).size().unstack(fill_value=0)
    shift_statistics = df.groupby(['employee_id', 'shift_type']).size().unstack(fill_value=0)

    # 合并进主表
    pivot = pivot.merge(status_statistics, how='left', on='employee_id')
    pivot = pivot.merge(shift_statistics, how='left', on='employee_id')

    df1 = df[df['day'].isin(weekends['Saturday'] + weekends['Sunday'] + weekends['is_holiday'])].groupby(['employee_id', 'attendance_status']).size().unstack(fill_value=0)


    # 缺失统计列补0（比如有些人没有事假或迟到等）
    for col in ['出勤', '迟到', '早退', '出差', '半天', '病假', '事假', '旷工', '夜班', '白班']:
        if col not in pivot.columns:
            pivot[col] = 0
        if col not in df1.columns:
            df1[col] = 0

        
    # 总出勤，工作日出勤，
    pivot['出勤'] = pivot['出勤'] + pivot['迟到'] + pivot['早退'] + pivot['出差'] + pivot['半天'] * 0.5
    df1['工作日出勤天数'] = df1['出勤'] + df1['迟到'] + df1['早退'] + df1['出差'] + df1['半天'] * 0.5
    pivot = pivot.merge(df1['工作日出勤天数'], how='left', on='employee_id')
    pivot['工作日出勤天数'] = pivot['出勤'] - pivot['工作日出勤天数']

    pivot = pivot.merge(df[['employee_id','name']].drop_duplicates(), how='left', on='employee_id')

    ordered_cols = ['employee_id', 'name'] + [f"{i:02d}" for i in range(1,max_day+1)] + ['出勤', '迟到', '早退', '病假', '事假', '旷工', '半天', '出差', '工作日出勤天数', '延时加班', '周六加班', '周日加班', '节假日加班', '夜班']
    pivot = pivot[ordered_cols]
    pivot = pivot.fillna('0')

    return pivot,max_day