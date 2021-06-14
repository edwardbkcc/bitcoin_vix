import datetime
import consts
import csv
from math import sqrt

#returns a list of a parsed date assumes
def parse_str_date(date,char_to_split_by):
    parsed_date = date.split(char_to_split_by)
    return parsed_date
def get_current_time():
    current_time = str(datetime.datetime.utcnow())
    return current_time
def find_fiscal_quarter(current_month):
    fiscal_quarter = 0
    if current_month <= 3:
        fiscal_quarter = 1
    elif current_month <= 6:
        fiscal_quarter = 2
    elif current_month <= 9:
        fiscal_quarter = 3
    elif current_month <= 12:
        fiscal_quarter = 4
    return fiscal_quarter

def find_options_months_needed(current_fiscal_quarter):
    list_of_options_months_needed = []
    if current_fiscal_quarter == 1:
        list_of_options_months_needed.append(consts.JUNE)
        list_of_options_months_needed.append(consts.SEPTEMBER)
    elif current_fiscal_quarter == 2:
        list_of_options_months_needed.append(consts.SEPTEMBER)
        list_of_options_months_needed.append(consts.DECEMBER)
    elif current_fiscal_quarter == 3:
        list_of_options_months_needed.append(consts.DECEMBER)
        list_of_options_months_needed.append(consts.MARCH)
    elif current_fiscal_quarter == 4:
        list_of_options_months_needed.append(consts.MARCH)
        list_of_options_months_needed.append(consts.JUNE)
    return list_of_options_months_needed

def parse_strike_price_from_insturment_name(instrument_name):
    base_currency, expiration, strike, type = instrument_name.split("-")
    strike = int(strike)
    return strike
def get_instrument_element(list_of_instruments,instrument_name,element):
    expiration_date = ''
    for index in range(len(list_of_instruments)):
        if list_of_instruments[index][consts.INSTRUMENT_NAME] == instrument_name:
            expiration_date = list_of_instruments[index][element]
    return expiration_date
def str_date_to_dtime_obj(str_date):
    date,clock,tz = str_date.split(" ")
    year,month,day = date.split("-")
    hour,minute,sec = clock.split(":")
    date_time_object = datetime.datetime(int(year),int(month),int(day),int(hour),int(minute),int(sec))
    return date_time_object
#professional way to calculate it (Same way vol traders calc.)
def time_till_expiration(expiry_date,current_time):
    time_till_expiration = expiry_date - current_time
    days_left = int(time_till_expiration.days)
    days_left_in_minutes = days_left * consts.MINUTES_IN_A_DAY
    minutes_and_sec_left = divmod(time_till_expiration.seconds, consts.MINUTES_IN_AN_HOUR)
    minutes_left = int(minutes_and_sec_left[0])
    time_until_expiry_in_mins = days_left_in_minutes + minutes_left
    #professional way to calculate time left
    time_until_expiration_adj = time_until_expiry_in_mins / consts.MINUTES_IN_A_YEAR
    return time_until_expiration_adj
def get_diffrence_between_call_and_put_price(call_midoint,put_midpoint):
    diffrence = abs(call_midoint - put_midpoint)
    return diffrence

def find_where_diffrence_is_smallest(list_of_option_chain_dict):
    diffrence = 1000000000
    value = 0
    for index in range(len(list_of_option_chain_dict)):
        if list_of_option_chain_dict[index][consts.DIFFRENCE] < diffrence:
            if list_of_option_chain_dict[index][consts.CALLMIDPOINT] != 0 and list_of_option_chain_dict[index][consts.PUTMIDPOINT] != 0:
                diffrence = list_of_option_chain_dict[index][consts.DIFFRENCE]
                value = index
    return value
def is_str(value):
    if isinstance(value,str):
        return True
    else:
        return False
def get_diffrence_in_strike(strike_1,strike_2):
    diffrence = abs(strike_1 - strike_2)
    return diffrence

def get_contribution_by_strike(diffrence_in_strikes,current_strike_squared,midpoint, riskfreerate, time_to_expiry,e):
    contribution_by_strike = ((diffrence_in_strikes / current_strike_squared) * (e ** (riskfreerate * time_to_expiry)) *
                              midpoint)
    return contribution_by_strike

def calc_second_part_in_vol_formula(time_to_expiry, foward_price, strike_price):
    calculation = (1 / (time_to_expiry)) * ((foward_price / strike_price) - 1) ** 2
    return calculation
def get_time_till_settlement(current_time,settlment_time):
    time_till_settlement = current_time - settlment_time
    days_left = int(time_till_settlement.days)
    days_left_in_minutes = days_left * consts.MINUTES_IN_A_DAY
    minutes_and_sec_left = divmod(time_till_settlement.seconds, consts.MINUTES_IN_AN_HOUR)
    minutes_left = int(minutes_and_sec_left[0])
    time_until_settlement_in_mins = days_left_in_minutes + minutes_left
    return time_until_settlement_in_mins
def calc_weighted_avg_vol(vol1,vol2,T1,T2,N225,N365,NT1,NT2):
    weighted_avg_front = ((NT2 - N225) / (NT2 - NT1)) * (T1 * vol1)
    weighted_avg_back = ((N225 - NT1) / (NT2 - NT1)) * (T2 * vol2)
    number_mins_stndized = N365 / N225
    weighted_avg = (weighted_avg_front + weighted_avg_back) * number_mins_stndized
    weighted_avg_final = sqrt(weighted_avg)
    return weighted_avg_final
def write_to_csv(cix_value):
    with open(consts.FILENAME, consts.APPEND) as file:
        writer = csv.writer(file)
        data = [str(datetime.datetime.utcnow()), str(cix_value)]
        writer.writerow(data)
    file.close()