import argparse
import pandas as pd
from collections import defaultdict


def process_age_group(age):
    if age < 18:
        return '18-'
    else:
        return '18+'

def process_region_group(prov_group):
    north_regions = ['Neimengol', 'Heilongjiang', 'Jilin', 'Liaoning', 'Beijing', 'Tianjin', 'Hebei', 'Shanxi', 'Shaanxi', 'Gansu', 'Ningxia', 'Henan', 'Shandong', 'Xinjiang']
    south_regions = ['Jiangsu', 'Anhui', 'Hubei', 'Sichuan', 'Chongqing', 'Yunnan', 'Guizhou', 'Guangxi', 'Guangdong', 'Fujian', 'Zhejiang', 'Jiangxi', 'Hunan', 'Hainan', 'Shanghai']
    if prov_group in north_regions:
        return 'N'
    elif prov_group in south_regions:
        return 'S'
    else:
        return 'XQ'

def read_txt_file(file_path):
    df = pd.read_csv(file_path, header=1, names=['Province', 'Time', 'InfectionSite', 'AgeGroup', 'Gender', 'BacteriaList', 'CaseCount'])
    df['AgeGroup'] = df['AgeGroup'].apply(process_age_group)
    df['Province'] = df['Province'].apply(process_region_group)
    df = df[df['Province'] != 'XQ']
    return df


def parse_arguments():
    parser = argparse.ArgumentParser(description="Process input files")
    parser.add_argument('input_file', type=str, help='Path to the input text file')
    parser.add_argument('List_file', type=str, help='Path to the List text file')
    return parser.parse_args()

def process_grouping(df, group_by):
    results = []
    grouped = df.groupby(group_by)
    
    for group_keys, group in grouped:
        if not isinstance(group_keys, tuple):
            group_keys = (group_keys,)
            
        total_cases = group['CaseCount'].sum()
        
        group['BacteriaList'] = group['BacteriaList'].fillna('')
        mp_group = group[group['BacteriaList'].str.contains('Mycoplasma pneumoniae')]
        nomp_group = group[~group['BacteriaList'].str.contains('Mycoplasma pneumoniae')]

        co_mp_cases = mp_group[mp_group['BacteriaList'].str.contains(';')]['CaseCount'].sum()
        s_mp_cases = mp_group[~mp_group['BacteriaList'].str.contains(';')]['CaseCount'].sum()
        non_mp_cases = total_cases - co_mp_cases - s_mp_cases
        
        bacteria_count_mp = defaultdict(int)
        bacteria_count_nomp = defaultdict(int)

        for _, row in mp_group.iterrows():
            bacteria_list = row['BacteriaList'].split(';')
            for bacteria in bacteria_list:
                if bacteria in blist and bacteria != ' Mycoplasma pneumoniae' and len(bacteria_list) != 1:
                    bacteria_count_mp[bacteria] += row['CaseCount']

        for _, row in nomp_group.iterrows():
            bacteria_list = row['BacteriaList'].split(';')
            for bacteria in bacteria_list:
                bacteria_count_nomp[bacteria] += row['CaseCount']

        top_10_bacteria = sorted(bacteria_count_mp.items(), key=lambda x: x[1], reverse=True)[:100]
        
        for bacteria, mp_count in top_10_bacteria:
            mp_rate = mp_count / co_mp_cases if co_mp_cases > 0 else 0
            nomp_rate = bacteria_count_nomp[bacteria] / non_mp_cases if non_mp_cases > 0 else 0
            results.append(list(group_keys) + [total_cases, co_mp_cases, s_mp_cases, non_mp_cases, bacteria, mp_count, mp_rate, nomp_rate, bacteria_count_nomp[bacteria]])
    
    return results

def write_to_excel(results, output_file, columns):
    output_df = pd.DataFrame(results, columns=columns)
    output_df.to_excel(output_file, index=False)

def main():
    args = parse_arguments()
    global blist
    blist = [line.strip() for line in open(args.List_file, 'r')]
    
    df = read_txt_file(args.input_file)
    
    groupings = {
        'Province': 'Province',
        'InfectionSite': 'InfectionSite',
        'AgeGroup': 'AgeGroup',
        'Gender': 'Gender'
    }
    
    columns = {
        'Province': ['Province', 'Total Cases', 'Co-MP Cases', 'S_MP Cases', 'Non-MP Cases', 'Bacteria', 'MP Count', 'Co-MP Rate', 'Non-MP Rate', 'Bacteria Count Non-MP'],
        'InfectionSite': ['InfectionSite', 'Total Cases', 'Co-MP Cases', 'S_MP Cases', 'Non-MP Cases', 'Bacteria', 'MP Count', 'Co-MP Rate', 'Non-MP Rate', 'Bacteria Count Non-MP'],
        'AgeGroup': ['AgeGroup', 'Total Cases', 'Co-MP Cases', 'S_MP Cases', 'Non-MP Cases', 'Bacteria', 'MP Count', 'Co-MP Rate', 'Non-MP Rate', 'Bacteria Count Non-MP'],
        'Gender': ['Gender', 'Total Cases', 'Co-MP Cases', 'S_MP Cases', 'Non-MP Cases', 'Bacteria', 'MP Count', 'Co-MP Rate', 'Non-MP Rate', 'Bacteria Count Non-MP']
    }
    
    for key, group_by in groupings.items():
        results = process_grouping(df, group_by)
        write_to_excel(results, f'result/{key}.xlsx', columns[key])

if __name__ == '__main__':
    main()