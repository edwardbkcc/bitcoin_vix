from deribit_api import RestClient
from CIX import CIX
import consts
import util
import datetime
import pandas as pd
from bkutils import df_to_csv

deribit = RestClient("KEY", "SECRET")
cix = CIX()

# edit options chain need to fill in ask and find new midpoint price so i can complete

#rest of step 1 on file
def get_option_chain(call_options_list,put_options_list,btc_price):
    option_chain_list = []
    #since call and put options list have same lenght only have to loopr through one
    for index in range(len(call_options_list)):
        option_chain_dict = {}
        #if there is no midpirce it means there are no sellers. Set ask equal to 0.
        if util.is_str(deribit.getsummary(call_options_list[index])[consts.MIDPRICE]) == False:
            call_midpoint = deribit.getsummary(call_options_list[index])[consts.MIDPRICE] * btc_price
            call_bid = deribit.getsummary(call_options_list[index])[consts.BIDPRICE] * btc_price
            call_ask = deribit.getsummary(call_options_list[index])[consts.ASKPRICE] * btc_price
        else:
            call_bid = 0
            call_ask = 0
            call_midpoint = 0
        # if there is no midpirce it means there are no sellers or buyers. Set ask equal to 0.
        if util.is_str(deribit.getsummary(put_options_list[index])[consts.MIDPRICE]) == False:
            put_midpoint = deribit.getsummary(put_options_list[index])[consts.MIDPRICE] * btc_price
            put_bid = deribit.getsummary(put_options_list[index])[consts.BIDPRICE] * btc_price
            put_ask = deribit.getsummary(put_options_list[index])[consts.ASKPRICE] * btc_price
        else:
            put_bid = 0
            put_ask = 0
            put_midpoint = 0
        diffrence = util.get_diffrence_between_call_and_put_price(call_midpoint, put_midpoint)
        strike = util.parse_strike_price_from_insturment_name(call_options_list[index])

        front_month_option_chain_dict = {consts.STRIKE: strike, consts.CALLMIDPOINT: call_midpoint, consts.PUTMIDPOINT: put_midpoint,
                                         consts.DIFFRENCE: diffrence, consts.CALLBID:call_bid, consts.CALLASK:call_ask,
                                         consts.PUTBID:put_bid,consts.PUTASK:put_ask}
        option_chain_list.append(front_month_option_chain_dict)
    return option_chain_list

def main():
    contracts = deribit.getinstruments()
    btc_price = deribit.index()[consts.BITCOININDEX]
    dict_options_contracts = cix.get_options_contracts(contracts)
    front_month_call_options_list_unsorted = dict_options_contracts[consts.FRONT_MONTH_CALL]
    front_month_put_options_list_unsorted = dict_options_contracts[consts.FRONT_MONTH_PUT]
    back_month_call_options_list_unsorted = dict_options_contracts[consts.BACK_MONTH_CALL]
    back_month_put_options_list_unsorted = dict_options_contracts[consts.BACK_MONTH_PUT]
    front_month_call_options_list_sorted = cix.sort_options_contracts_by_strike(front_month_call_options_list_unsorted)
    front_month_put_options_list_sorted = cix.sort_options_contracts_by_strike(front_month_put_options_list_unsorted)
    back_month_call_options_list_sorted = cix.sort_options_contracts_by_strike(back_month_call_options_list_unsorted)
    back_month_put_options_list_sorted = cix.sort_options_contracts_by_strike(back_month_put_options_list_unsorted)
    front_month_time_to_expiry = cix.get_time_to_expiration(contracts,front_month_call_options_list_sorted[0])
    back_month_time_to_expiry = cix.get_time_to_expiration(contracts,back_month_call_options_list_sorted[0])
    front_month_time_to_settlement = cix.get_time_to_settlement(contracts,front_month_call_options_list_sorted[0])
    back_month_time_to_settlement = cix.get_time_to_settlement(contracts,back_month_call_options_list_sorted[0])
    #assumes equal strikes for both calls and puts
    option_chain_front_month = get_option_chain(front_month_call_options_list_sorted,
                                                                 front_month_put_options_list_sorted,btc_price)
    option_chain_back_month = get_option_chain(back_month_call_options_list_sorted,
                                                                 back_month_put_options_list_sorted,btc_price)
    index_value_of_front_month_option_chain = util.find_where_diffrence_is_smallest(option_chain_front_month)
    index_value_of_back_month_option_chain = util.find_where_diffrence_is_smallest(option_chain_back_month)
    front_month_foward_price = cix.get_foward_price(option_chain_front_month[index_value_of_front_month_option_chain],
                                                    front_month_time_to_expiry, consts.RISKFREEFRONTMNTH)

    back_month_foward_price = cix.get_foward_price(option_chain_front_month[index_value_of_back_month_option_chain],
                                                    back_month_time_to_expiry, consts.RISKFREEBACKMNTH)
    front_month_strike = cix.get_strike_below_foward_price(front_month_foward_price, option_chain_front_month)
    back_month_strike = cix.get_strike_below_foward_price(back_month_foward_price, option_chain_back_month)
    front_month_put_call_avg = cix.get_put_call_avg(option_chain_front_month, front_month_strike)
    back_month_put_call_avg = cix.get_put_call_avg(option_chain_back_month, back_month_strike)
    front_month_strike_contrib = cix.get_sum_of_contribution_by_strikes(option_chain_list=option_chain_front_month,
                                                                              call_put_avg=front_month_put_call_avg,
                                                                              riskfreerate=consts.RISKFREEFRONTMNTH,
                                                                              strike=front_month_strike,
                                                                              time_to_expiry=front_month_time_to_expiry)
    back_month_strike_contrib = cix.get_sum_of_contribution_by_strikes(option_chain_list=option_chain_back_month,
                                                                              call_put_avg=back_month_put_call_avg,
                                                                              riskfreerate=consts.RISKFREEBACKMNTH,
                                                                              strike=back_month_strike,
                                                                              time_to_expiry=back_month_time_to_expiry)
    front_month_vol = cix.get_volatility(front_month_strike_contrib,
                                         cix.get_second_part_of_vol_calc(front_month_time_to_expiry,
                                                                         front_month_foward_price, front_month_strike))
    back_month_vol = cix.get_volatility(back_month_strike_contrib,
                                         cix.get_second_part_of_vol_calc(back_month_time_to_expiry,
                                                                         back_month_foward_price, back_month_strike))
    weighted_average_vols = cix.get_weighted_average_of_volatilites(front_month_vol=front_month_vol,
                                                                    back_month_vol=back_month_vol,
                                                                    back_mnth_time_to_expiry=back_month_time_to_expiry,
                                                                    front_mnth_time_to_expiry=front_month_time_to_expiry,
                                                                    mins_in_225_days=consts.MINUTES_IN_225_DAYS,
                                                                    mins_in_year=consts.MINUTES_IN_A_YEAR,
                                                                    time_till_front_mnth_settlement=front_month_time_to_settlement,
                                                                    time_till_back_month_settlmenet=back_month_time_to_settlement)
    value_of_cix = cix.calc_CIX(weighted_average_vols)

    bvix_list = [[datetime.datetime.now().date(),value_of_cix]]
    bvix_df = pd.DataFrame(bvix_list, columns = [consts.TIMESTAMP,consts.VALUE])
    bvix_df.set_index(consts.TIMESTAMP,inplace=True)
    df_to_csv.df_to_csv(bvix_df,[consts.VALUE],consts.FILENAME)

main()
