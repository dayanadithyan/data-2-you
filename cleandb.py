import pandas as pd

def splice_first_10_rows_pandas(input_file, output_file=None):
    """
    Extract the first 10 rows from a CSV file using pandas.
    
    Parameters:
    input_file (str): Path to the input CSV file
    output_file (str, optional): Path to save the output CSV file. 
                               If None, returns the DataFrame.
    
    Returns:
    DataFrame: First 10 rows of the CSV if output_file is None
    bool: True if successful in writing to output_file
    """
    try:
        # Read the first 10 rows of the CSV file
        df = pd.read_csv(input_file, nrows=10)
        
        # If output file is specified, write the dataframe to it
        if output_file:
            df.to_csv(output_file, index=False)
            return True
        
        # Otherwise, return the dataframe
        return df
    
    except Exception as e:
        print(f"Error: {e}")
        return None
    
splice_first_10_rows_pandas('/Volumes/LNX/NEW/data2/exs.csv','/Volumes/LNX/NEW/data2/ccexs.csv')