import pandas as pd
import sys
from itertools import product

def parse_arguments():
    if len(sys.argv) != 3:
        print("Usage: python script.py <inputfile> <outputfile>")
        sys.exit(1)
    return sys.argv[1], sys.argv[2]

def read_and_prepare_data(inputfile):
    df = pd.read_excel(inputfile)
    df['dates'] = pd.to_datetime(df['dates'])
    df['month'] = df['dates'].dt.strftime('%Y-%m')
    return df

def add_missing_months_and_calculate_aap(group):
    # Create a complete list of months from 2023-01 to 2024-05
    all_months = pd.date_range(start='2023-01', end='2024-05', freq='M').strftime('%Y-%m').tolist()
    
    # Identify missing months in the group
    existing_months = group['month'].tolist()
    missing_months = [month for month in all_months if month not in existing_months]
    
    # Create DataFrame for missing months
    missing_data = pd.DataFrame({
        'month': missing_months,
        'prov': group['prov'].iloc[0],
        'Normalized Cases': 0,
        'Normalized MP Cases': 0,
        'Normalized Positivity Rate': 0
    })
    
    # Concatenate existing group with the missing data
    group = pd.concat([group, missing_data], ignore_index=True)
    group = group[(group['month'] >= '2023-04') & (group['month'] <= '2024-03')]#2023-04 to 2024-03
    # Recalculate AAP
    total_positivity_rate = group['Normalized Positivity Rate'].sum()
    group['AAP'] = group['Normalized Positivity Rate'] / total_positivity_rate if total_positivity_rate > 0 else 0
    
    # Sort by month for consistency
    group = group.sort_values(by='month').reset_index(drop=True)
    
    return group

def calculate_cum_aap_and_ep(group):
    group = group.sort_values(by='AAP', ascending=False).reset_index(drop=True)
    group['CumAAP'] = group['AAP'].cumsum()
    group['Epidemic'] = [(1 if cum_aap <= 0.75 else round((0.75 - group.at[i-1, 'CumAAP']) / app, 5)) if i > 0 and cum_aap > 0.75 and group.at[i-1, 'CumAAP'] < 0.75 else (1 if cum_aap <= 0.75 else 0) for i, (cum_aap, app) in enumerate(zip(group['CumAAP'], group['AAP']))]
    return group

def update_status(group):
    epidemic_rows = group[group['status'] == 'Epidemic']
    if epidemic_rows.empty:
        return group
    
    epidemic_rows = epidemic_rows.sort_values(by='month')
    epidemic_rows['month'] = pd.to_datetime(epidemic_rows['month'])
    epidemic_rows['group'] = (epidemic_rows['month'].diff().dt.days > 62).cumsum()
    longest_group = epidemic_rows['group'].value_counts().idxmax()
    earliest_epidemic = epidemic_rows[epidemic_rows['group'] == longest_group].iloc[0]
    group.at[earliest_epidemic.name, 'status'] = 'onset'
    return group

def main():
    inputfile, outputfile = parse_arguments()
    df = read_and_prepare_data(inputfile)
    df = df.groupby('prov').apply(add_missing_months_and_calculate_aap).reset_index(drop=True)
    df = df.groupby('prov').apply(calculate_cum_aap_and_ep).reset_index(drop=True)
    df['status'] = df['Epidemic'].apply(lambda x: 'Non-epidemic' if x == 0 else 'Epidemic')
    df = df.groupby('prov',group_keys=True).apply(update_status)
    df.to_excel(outputfile, index=False)

if __name__ == "__main__":
    main()