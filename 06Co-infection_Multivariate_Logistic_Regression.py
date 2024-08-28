import pandas as pd
import statsmodels.api as sm
import argparse
import sys
import numpy as np

def read_data(file_path):
    """Reads data from a file with different formats: CSV, TXT, Excel"""
    if file_path.endswith('.csv'):
        return pd.read_csv(file_path)
    elif file_path.endswith('.txt'):
        return pd.read_csv(file_path, sep='\t')
    elif file_path.endswith('.xls') or file_path.endswith('.xlsx'):
        return pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format. Please input a csv, txt, or xls/xlsx file.")

def main(input_file, output_file, sample_fraction):
    # Read data file
    try:
        data = read_data(input_file)
    except Exception as e:
        print(f"Failed to read input file: {e}")
        sys.exit(1)

    # Define dependent variable
    y = data['Mycoplasma pneumoniae']

    # Define covariates
    covariates = ['region', 'site', 'age', 'sex']

    # Define independent variables (excluding covariates and dependent variable)
    bacteria_vars = [col for col in data.columns if col not in covariates + ['Mycoplasma pneumoniae'] + ['date']]

    # Create an empty DataFrame to store results
    results = pd.DataFrame(columns=['Bacteria', 'Coefficient', 'P-value', 'Std Err', 'Z', 'CI Lower (0.025)', 'CI Upper (0.975)'])

    # Randomly sample data for analysis based on specified fraction
    sample_data = data.sample(frac=sample_fraction, random_state=1)
    sample_y = sample_data['Mycoplasma pneumoniae']

    # Loop through each bacteria variable
    for bacteria in bacteria_vars:
        # Define the current independent variable
        X = sample_data[covariates + [bacteria]]

        # Add constant
        X = sm.add_constant(X)

        try:
            # Fit model only if it converges
            model = sm.Logit(sample_y, X).fit()

            # Extract coefficients and p-values
            coef = model.params[bacteria]
            p_value = model.pvalues[bacteria]
            std_err = model.bse[bacteria]
            z_value = model.tvalues[bacteria]
            ci_lower, ci_upper = model.conf_int().loc[bacteria]

            # Append result to the results DataFrame
            results = results.append({
                'Bacteria': bacteria,
                'Coefficient': coef,
                'P-value': p_value,
                'Std Err': std_err,
                'Z': z_value,
                'CI Lower (0.025)': ci_lower,
                'CI Upper (0.975)': ci_upper
            }, ignore_index=True)
        except Exception as e:
            print(f"Failed to fit model for {bacteria}: {e}")

    # Output results to the specified file
    try:
        results.to_csv(output_file, sep='\t', index=False)
        print(f"Results successfully saved to {output_file}")
    except Exception as e:
        print(f"Failed to write output file: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Bacteria Analysis Tool')
    parser.add_argument('input_file', type=str, help='Input data file (csv, txt, xlsx format)')
    parser.add_argument('output_file', type=str, help='Output file (csv format)')
    parser.add_argument('-f', '--fraction', type=float, default=1, help='Sample fraction (0-1) for analysis, default is 1 (use all data)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.0', help="Show program's version number and exit")
    
    args = parser.parse_args()

    # Check if the sample fraction is within the valid range
    if not (0 <= args.fraction <= 1):
        print("Error: Sample fraction must be between 0 and 1.")
        sys.exit(1)

    # Execute main function
    main(args.input_file, args.output_file, args.fraction)