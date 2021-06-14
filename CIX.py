import datetime
import util
import consts
from math import e
class CIX():
    def __init__(self):
        pass
    #returns a list of the call and put options needed
    def get_options_contracts(self,a_list_of_instruments):
        #Get current time and fiscal quarters
        front_month_call_options_contracts = []
        front_month_put_options_contracts = []
        back_month_call_options_contracts = []
        back_month_put_options_contracts = []
        dict_options_contracts = []
        current_time = util.get_current_time()
        current_time_list = util.parse_str_date(current_time," ")
        current_date = current_time_list[0]
        year_month_date = util.parse_str_date(current_date,"-")
        current_month = int(year_month_date[1])
        current_fiscal_quarter = util.find_fiscal_quarter(current_month)
        options_months_needed = util.find_options_months_needed(current_fiscal_quarter)
        #Loop through bitcoin contracts and find option expirations which are 2Q and 3Q away from expiration.
        #example if we are in Q1 we want to find option contracts from Q3 and Q4 to use
        for index in range(len(a_list_of_instruments)):
            if (a_list_of_instruments[index][consts.KIND] == consts.OPTION) and (a_list_of_instruments[index][consts.BASE_CURRENCY] ==
                                                                                     consts.BITCOIN):
                exp_date,exp_time,tz = util.parse_str_date(a_list_of_instruments[index][consts.EXPIRATION]," ")
                exp_day,exp_month,exp_year = util.parse_str_date(exp_date, "-")
                expiration_month = int(exp_month)
                if (options_months_needed[0] == expiration_month) and a_list_of_instruments[index][consts.TYPE] == consts.CALL:
                    front_month_call_options_contracts.append(a_list_of_instruments[index][consts.INSTRUMENT_NAME])
                elif (options_months_needed[0] == expiration_month) and a_list_of_instruments[index][consts.TYPE] == consts.PUT:
                    front_month_put_options_contracts.append(a_list_of_instruments[index][consts.INSTRUMENT_NAME])
                elif (options_months_needed[1] == expiration_month) and a_list_of_instruments[index][consts.TYPE] == consts.CALL:
                    back_month_call_options_contracts.append(a_list_of_instruments[index][consts.INSTRUMENT_NAME])
                elif (options_months_needed[1] == expiration_month) and a_list_of_instruments[index][consts.TYPE] == consts.PUT:
                    back_month_put_options_contracts.append(a_list_of_instruments[index][consts.INSTRUMENT_NAME])
        dict_options_contracts = {consts.FRONT_MONTH_CALL:front_month_call_options_contracts, consts.FRONT_MONTH_PUT:front_month_put_options_contracts,
                                  consts.BACK_MONTH_CALL:back_month_call_options_contracts, consts.BACK_MONTH_PUT:back_month_put_options_contracts}
        return dict_options_contracts
    #sorts contracts from smallest strike to largest strike in ascenindg order (like an option chain)
    def sort_options_contracts_by_strike(self,a_list_of_options_contract):
        list_of_strikes = []
        list_of_sorted_options = []
        #loop through options contract names and parse the strikes
        for index in range(len(a_list_of_options_contract)):
            strike = util.parse_strike_price_from_insturment_name(a_list_of_options_contract[index])
            list_of_strikes.append(strike)
        list_of_strikes.sort()
        #Sort options name list based on options strikes in ascending order
        for index in range(len(list_of_strikes)):
            for index_2 in range(len(a_list_of_options_contract)):
                strike = util.parse_strike_price_from_insturment_name(a_list_of_options_contract[index_2])
                if list_of_strikes[index] == strike:
                    list_of_sorted_options.append(a_list_of_options_contract[index_2])

        return list_of_sorted_options

    #same calculation vix and professional traders use for volatility
    def get_time_to_expiration(self, list_of_instruments, an_option_contract_name):
        expiration_date_str= util.get_instrument_element(list_of_instruments, an_option_contract_name,consts.EXPIRATION)
        expiration_date_dt = util.str_date_to_dtime_obj(expiration_date_str)
        current_time_dt = datetime.datetime.utcnow()
        time_till_expiration = util.time_till_expiration(expiration_date_dt,current_time_dt)
        return time_till_expiration
    def get_time_to_settlement(self,list_of_instruments, an_option_contract_name):
        settlement_date_str = util.get_instrument_element(list_of_instruments, an_option_contract_name,consts.EXPIRATION)
        settlement_date_dt = util.str_date_to_dtime_obj(settlement_date_str)
        current_time_dt = datetime.datetime.utcnow()
        time_till_settlement = util.get_time_till_settlement(settlement_date_dt, current_time_dt)
        return time_till_settlement
    def get_foward_price(self,list_of_option_data,time_to_expiry,riskfreerate):
        strike_price = list_of_option_data[consts.STRIKE]
        call_price = list_of_option_data[consts.CALLMIDPOINT]
        put_price = list_of_option_data[consts.PUTMIDPOINT]
        time = time_to_expiry
        diffrence = call_price - put_price
        foward_price = strike_price + (e ** (riskfreerate * time)) * diffrence
        return foward_price
    def get_strike_below_foward_price(self, foward_price, option_chain):
        strike = 0
        for index in range(len(option_chain)):
            if foward_price < option_chain[index][consts.STRIKE]:
                strike = option_chain[index - 1][consts.STRIKE]
                break
        return strike
    def get_put_call_avg(self, option_chain_list, strike):
        put_call_avg = 0
        for index in range(len(option_chain_list)):
            if option_chain_list[index][consts.STRIKE] == strike:
                put_call_avg = (option_chain_list[index][consts.CALLMIDPOINT] + option_chain_list[index][consts.PUTMIDPOINT])/2
                break
        return put_call_avg

    def get_sum_of_contribution_by_strikes(self,option_chain_list,call_put_avg,time_to_expiry,strike,riskfreerate):
        list_of_strike_contributions = []
        contribution_by_strike = 0
        sum_of_contributions = 0
        for index in range(len(option_chain_list)):
            #if strike is less than our monthly strike price calculate contribtuion of OTM put options by strike
            if strike > option_chain_list[index][consts.STRIKE]:
                if index == 0:
                    diffrence_in_strikes = util.get_diffrence_in_strike(option_chain_list[index][consts.STRIKE],
                                                                        option_chain_list[index + 1][consts.STRIKE])
                    current_strike_squared = option_chain_list[index][consts.STRIKE]**2
                    midpoint = option_chain_list[index][consts.PUTMIDPOINT]
                    contribution_by_strike = util.get_contribution_by_strike(diffrence_in_strikes,current_strike_squared,
                                                                             midpoint, riskfreerate, time_to_expiry,e)
                else:
                    #diffrence in strikes is the only change
                    diffrence_in_strikes = util.get_diffrence_in_strike(option_chain_list[index - 1][consts.STRIKE],
                                                                        option_chain_list[index + 1][consts.STRIKE])
                    current_strike_squared = option_chain_list[index][consts.STRIKE] ** 2
                    midpoint = option_chain_list[index][consts.PUTMIDPOINT]
                    contribution_by_strike = util.get_contribution_by_strike(diffrence_in_strikes,
                                                                             current_strike_squared,
                                                                             midpoint, riskfreerate, time_to_expiry, e)
            elif strike < option_chain_list[index][consts.STRIKE]:
                if index == len(option_chain_list)-1:
                    diffrence_in_strikes = util.get_diffrence_in_strike(option_chain_list[index][consts.STRIKE],
                                                                        option_chain_list[index - 1][consts.STRIKE])
                    current_strike_squared = option_chain_list[index][consts.STRIKE]**2
                    midpoint = option_chain_list[index][consts.CALLMIDPOINT]
                    contribution_by_strike = util.get_contribution_by_strike(diffrence_in_strikes,current_strike_squared,
                                                                             midpoint, riskfreerate, time_to_expiry,e)
                else:
                    #diffrence in strikes is the only change
                    diffrence_in_strikes = util.get_diffrence_in_strike(option_chain_list[index - 1][consts.STRIKE],
                                                                        option_chain_list[index + 1][consts.STRIKE])
                    current_strike_squared = option_chain_list[index][consts.STRIKE] ** 2
                    midpoint = option_chain_list[index][consts.CALLMIDPOINT]
                    contribution_by_strike = util.get_contribution_by_strike(diffrence_in_strikes,
                                                                             current_strike_squared,
                                                                             midpoint, riskfreerate, time_to_expiry, e)
            #strike equal current monthly strike
            else:
                if index == 0:
                    diffrence_in_strikes = util.get_diffrence_in_strike(option_chain_list[index][consts.STRIKE],
                                                                        option_chain_list[index + 1][consts.STRIKE])
                    current_strike_squared = option_chain_list[index][consts.STRIKE]**2
                    midpoint = call_put_avg
                    contribution_by_strike = util.get_contribution_by_strike(diffrence_in_strikes,current_strike_squared,
                                                                             midpoint, riskfreerate, time_to_expiry,e)
                else:
                    #diffrence in strikes is the only change
                    diffrence_in_strikes = util.get_diffrence_in_strike(option_chain_list[index - 1][consts.STRIKE],
                                                                        option_chain_list[index + 1][consts.STRIKE])
                    current_strike_squared = option_chain_list[index][consts.STRIKE] ** 2
                    midpoint = call_put_avg
                    contribution_by_strike = util.get_contribution_by_strike(diffrence_in_strikes,
                                                                             current_strike_squared,
                                                                             midpoint, riskfreerate, time_to_expiry, e)
            list_of_strike_contributions.append(contribution_by_strike)
        sum_of_contributions = (2 / time_to_expiry) * sum(list_of_strike_contributions)
        return sum_of_contributions

    def get_second_part_of_vol_calc(self, time_to_expiry, foward_price, strike_price):
        value = util.calc_second_part_in_vol_formula(foward_price=foward_price, strike_price=strike_price,
                                                     time_to_expiry=time_to_expiry)
        return value
    def get_volatility(self,strike_contrib, secnd_vol_valc):
        volatility = strike_contrib - secnd_vol_valc
        return volatility

    def get_weighted_average_of_volatilites(self,front_month_vol,back_month_vol,front_mnth_time_to_expiry,
                                            back_mnth_time_to_expiry,mins_in_225_days,mins_in_year,
                                            time_till_front_mnth_settlement,time_till_back_month_settlmenet):
        vol_1 = front_month_vol
        vol_2 = back_month_vol
        T_1 = front_mnth_time_to_expiry
        T_2 = back_mnth_time_to_expiry
        N_225 = mins_in_225_days
        N_365 = mins_in_year
        NT_1 = time_till_front_mnth_settlement
        NT_2 = time_till_back_month_settlmenet
        weighted_avg = util.calc_weighted_avg_vol(vol_1, vol_2, T_1, T_2, N_225, N_365, NT_1, NT_2)
        return weighted_avg
    def calc_CIX(self,weighted_avg_vols):
        cix_val = weighted_avg_vols * 100
        return cix_val









