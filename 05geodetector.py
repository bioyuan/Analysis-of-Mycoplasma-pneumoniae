
import numpy as np
import pandas as pd
from typing import Union, Sequence
from scipy.stats import f, ncf
import warnings
import sys
import argparse

# Ignore specific types of warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

def check_data(df, y, factors):
    for factor in factors:
        if not factor in df.columns:
            raise ValueError(f'Factor [{factor}] is not in data')
    
    if y not in df.columns:
        raise ValueError(f'Factor [{y}] is not in data')
        
    for factor in factors:
        if y == factor:
            raise ValueError("Y variable should not be in Factor variables.")
    
    if df.isnull().values.any():
        raise ValueError("Data contains NULL values")

def cal_ssw(df: pd.DataFrame, y, factor, extra_factor=None):
    def _cal_ssw(df: pd.DataFrame, y):
        length = df.shape[0]
        if length == 1:
            strataVar = 0
            lamda_1st = np.square(df[y].values[0])
            lamda_2nd = df[y].values[0]
        else:
            strataVar = (length-1) * df[y].var(ddof=1)
            lamda_1st = np.square(df[y].values.mean())
            lamda_2nd = np.sqrt(length) * df[y].values.mean()
        return strataVar, lamda_1st, lamda_2nd

    if extra_factor is None:
        df2 = df[[y, factor]].groupby(factor).apply(_cal_ssw, y=y)
    else:
        df2 = df[[y] + list(set([factor, extra_factor]))].groupby([factor, extra_factor]).apply(_cal_ssw, y=y)

    df2 = df2.apply(pd.Series).sum()
    strataVarSum, lamda_1st_sum, lamda_2nd_sum = df2.values
    return strataVarSum, lamda_1st_sum, lamda_2nd_sum

def cal_q(df, y, factor, extra_factor=None):
    strataVarSum, lamda_1st_sum, lamda_2nd_sum = cal_ssw(df, y, factor, extra_factor)
    TotalVar = (df.shape[0]-1) * df[y].var(ddof=1)
    q = 1 - strataVarSum / TotalVar
    return q, lamda_1st_sum, lamda_2nd_sum

def factor_detector(df: pd.DataFrame, y: Union[str, int], factors: Sequence):
    check_data(df, y, factors=factors)

    out_df = pd.DataFrame(index=["q statistic", "p value"], columns=factors, dtype="float32")
    N_var = df[y].var(ddof=1)
    N_popu = df.shape[0]

    for factor in factors:
        N_stra = df[factor].unique().shape[0]
        q, lamda_1st_sum, lamda_2nd_sum = cal_q(df, y, factor)

        # Lambda value
        lamda = (lamda_1st_sum - np.square(lamda_2nd_sum) / N_popu) / N_var
        # F value
        F_value = (N_popu - N_stra) * q / ((N_stra - 1) * (1 - q))
        # p value
        p_value = ncf.sf(F_value, N_stra - 1, N_popu - N_stra, nc=lamda)

        out_df.loc["q statistic", factor] = q
        out_df.loc["p value", factor] = p_value
    
    return out_df

def interaction_relationship(df):
    out_df = pd.DataFrame(index=df.index, columns=df.columns)
    length = len(df.index)
    
    for i in range(length):
        for j in range(i+1, length):
            factor1, factor2 = df.index[i], df.index[j]
            i_q = df.loc[factor2, factor1]
            q1 = df.loc[factor1, factor1]
            q2 = df.loc[factor2, factor2]

            if i_q <= q1 and i_q <= q2:
                outputRls = "Weaken, nonlinear"
            elif i_q < max(q1, q2) and i_q > min(q1, q2):
                outputRls = "Weaken, uni-"
            elif i_q == (q1 + q2):
                outputRls = "Independent"
            elif i_q > max(q1, q2):
                outputRls = "Enhance, bi-"
            elif i_q > (q1 + q2):
                outputRls = "Enhance, nonlinear"

            out_df.loc[factor2, factor1] = outputRls
    
    return out_df

def interaction_detector(df: pd.DataFrame, y: Union[str, int], factors: Sequence, relationship=False):
    check_data(df, y, factors=factors)

    out_df = pd.DataFrame(index=factors, columns=factors, dtype="float32")
    length = len(factors)
    
    for i in range(length):
        for j in range(i + 1):
            q, _, _ = cal_q(df, y, factors[i], factors[j])
            out_df.loc[factors[i], factors[j]] = q

    if relationship:
        out_df2 = interaction_relationship(out_df)
        return out_df, out_df2
    
    return out_df

def ecological_detector(df: pd.DataFrame, y: Union[str, int], factors: Sequence):
    check_data(df, y, factors=factors)
    out_df = pd.DataFrame(index=factors, columns=factors, dtype="float32")
    length = len(factors)
    
    for i in range(1, length):
        ssw1, _, _ = cal_ssw(df, y, factors[i])
        dfn = df[factors[i]].notna().sum() - 1
        
        for j in range(i):
            ssw2, _, _ = cal_ssw(df, y, factors[j])
            dfd = df[factors[j]].notna().sum() - 1
            fval = (dfn * (dfd - 1) * ssw1) / (dfd * (dfn - 1) * ssw2)
            
            if fval < f.ppf(0.05, dfn, dfn):
                out_df.loc[factors[i], factors[j]] = 'Y'
            else:
                out_df.loc[factors[i], factors[j]] = 'N'

    return out_df

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Data Analysis Tool')
    parser.add_argument('input_file', metavar='input_file', type=str, help='Input data file (XLSX format)')
    parser.add_argument('output_file', metavar='output_file', type=str, help='Output file (XLSX or xls format)')
    args = parser.parse_args()
    
    # Print help if no arguments provided
    if not (args.input_file and args.output_file):
        parser.print_help()
        sys.exit(1)
        
    # Read input data
    df = pd.read_excel(args.input_file)
    columns = df.columns
    
    # Set parameters for factor detection
    target_column = columns[0]  # First column as y value
    factor_columns = columns[1:]  # Remaining columns as factor variables

    # Perform factor detection
    df_fd = factor_detector(df, target_column, factor_columns)

    # Perform interaction detection
    df1, df2 = interaction_detector(df, target_column, factor_columns, relationship=True)

    # Perform ecological detection
    df_ed = ecological_detector(df, target_column, factor_columns)

    # Output results to specified file
    with pd.ExcelWriter(args.output_file) as writer:
        df_fd.to_excel(writer, sheet_name='Factor Detection', index=True)
        df1.to_excel(writer, sheet_name='Interaction Detection 1', index=True)
        df2.to_excel(writer, sheet_name='Interaction Detection 2', index=True)
        df_ed.to_excel(writer, sheet_name='Ecological Detection', index=True)