import pandas as pd
import numpy as np
import random
import argparse


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Normalize case data.')
    parser.add_argument('input_file', type=str, help='Path to the input Excel file')
    parser.add_argument('output_file', type=str, help='Path to the output Excel file')
    parser.add_argument("-k", type=int, help='Number of times to repeat the random sampling')
    return parser.parse_args()

def normalize_cases(row):
    """
    Normalize the number of cases and positive cases.

    :param row: DataFrame row
    :return: Series with normalized case count, normalized positive cases, and normalized positive rate
    """
    args = parse_arguments()
    try:
        if row['Cases'] > 1000:
            # Case count is larger than 1000, perform random sampling
            positive_cases = []
            for _ in range(args.k):
                selected_cases = random.sample(range(row['Cases']), 1000  )
                positive_cases.append(sum(1 for _ in range(1000) if random.choice(selected_cases) < row['MP Cases']))
            normalized_positive_cases = np.median(positive_cases)
            return pd.Series([1000, normalized_positive_cases, normalized_positive_cases / 1000],
                             index=['Normalized Cases', 'Normalized MP Cases', 'Normalized Positivity Rate'])
        else:
            # Case count is less than or equal to 1000, scale up the total case count to 1000
            normalized_positive_cases = int(row['Positivity Rate'] * 1000)
            return pd.Series([1000, normalized_positive_cases, row['Positivity Rate']], index=['Normalized Cases', 'Normalized MP Cases', 'Normalized Positivity Rate'])
    except Exception as e:
        print(f"Error normalizing row: {row} - {e}")
        return pd.Series([np.nan, np.nan, np.nan], index=['Normalized Cases', 'Normalized MP Cases', 'Normalized Positivity Rate'])

def main():
    # Parse command line arguments
    args = parse_arguments()
    try:
        # Read the input Excel file
        df = pd.read_excel(args.input_file)
    except Exception as e:
        print(f"Error reading input file {args.input_file} - {e}")
        return
    try:
        # Apply the normalization function to each row
        normalized_df = df.apply(normalize_cases, axis=1)
    except Exception as e:
        print(f"Error during normalization - {e}")
        return        
    final_df = pd.concat([df, normalized_df], axis=1)# Combine the original DataFrame with the normalized data
    final_df.to_excel(args.output_file, index=False) # Write the result to the output Excel file
    
if __name__ == '__main__':
    main()
    
        
