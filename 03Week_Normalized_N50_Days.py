import pandas as pd
import numpy as np
import argparse

def read_and_prepare_data(inputfile):
    df = pd.read_csv(inputfile)
    df['days'] = pd.to_datetime(df['days'])
    return df

def fill_missing_dates(group, full_date_range):
    full_range_df = pd.DataFrame(full_date_range, columns=['days'])
    filled_group = full_range_df.merge(group, on='days', how='left')
    filled_group['Day_Cases'].fillna(0, inplace=True)
    filled_group['Day_MP_Cases'].fillna(0, inplace=True) 
    province_value = group['prov'].iloc[0]
    filled_group['prov'].fillna(province_value, inplace=True)
    return filled_group

def calculate_rolling_averages(group):
    group = group.sort_values(by='days').reset_index(drop=True)
    group['Average_Day_Cases'] = group['Day_Cases'].rolling(window=7, min_periods=1, center=True).mean().astype(int)
    group['Average_Day_MP_Cases'] = group['Day_MP_Cases'].rolling(window=7, min_periods=1, center=True).mean().astype(int)
    group['Average_Day_Positivity_Rate'] = group['Average_Day_MP_Cases'] / group['Average_Day_Cases']
    return group

def calculate_n50_days(group):
    group = group.sort_values(by='Average_Day_Positivity_Rate', ascending=False).reset_index(drop=True)
    total_positivity_rate = group['Average_Day_Positivity_Rate'].sum()
    cumulative_sum = group['Average_Day_Positivity_Rate'].cumsum()
    n50_days = (cumulative_sum <= total_positivity_rate / 2).sum()
    return n50_days

def main(inputfile, outputfile1, outputfile2):
    df = read_and_prepare_data(inputfile)
    global_min_date = df['days'].min()
    global_max_date = df['days'].max()
    full_date_range = pd.date_range(start=global_min_date, end=global_max_date)
    #print(full_date_range)
    df = df.groupby('prov').apply(fill_missing_dates, full_date_range=full_date_range).reset_index(drop=True)
    df = df.groupby('prov').apply(calculate_rolling_averages).reset_index(drop=True)
    
    results = []
    n50_results = []

    for prov, group in df.groupby('prov'):
        n50_days = calculate_n50_days(group)
        results.append(group)
        n50_results.append({'prov': prov, 'N50Days': n50_days})
    
    final_df = pd.concat(results).sort_values(by=['prov', 'days']).reset_index(drop=True)
    final_n50_df = pd.DataFrame(n50_results)

    # Write to output files
    final_df.to_csv(outputfile1, index=False, columns=['prov', 'days', 'Day_Cases', 'Day_MP_Cases', 'Average_Day_Cases', 'Average_Day_MP_Cases', 'Average_Day_Positivity_Rate'])
    final_n50_df.to_csv(outputfile2, index=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process and analyze COVID data per province.')
    parser.add_argument('inputfile', type=str, help='Input CSV file with columns: prov, days, Day_Cases, Day_MP_Cases')
    parser.add_argument('outputfile1', type=str, help='Output CSV file for detailed results')
    parser.add_argument('outputfile2', type=str, help='Output CSV file for N50 days results')

    args = parser.parse_args()
    main(args.inputfile, args.outputfile1, args.outputfile2)