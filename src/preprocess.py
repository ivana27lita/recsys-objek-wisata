import pandas as pd
import numpy as np
import pickle
from sklearn.preprocessing import OneHotEncoder
import os

def preprocess_data(tourism_path, user_path, rating_path, output_dir, models_dir):
    """
    Preprocess the raw data files and save the processed files.
    
    Args:
        tourism_path: Path to the tourism data
        user_path: Path to the user data
        rating_path: Path to the rating data
        output_dir: Directory to save processed data
        models_dir: Directory to save model files
    """
    # Create output directories if they don't exist
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)
    
    # Load data
    data_tourism = pd.read_csv(tourism_path)
    df_users = pd.read_csv(user_path)
    df_ratings = pd.read_csv(rating_path)
    
    # Process tourism data
    data_tourism_processed = data_tourism.drop(
        ['Price', 'Rating', 'Time_Minutes', 'Coordinate', 'Lat', 'Long', 'Unnamed: 11', 'Unnamed: 12'],
        axis=1,
        errors='ignore'
    )
    
    # Process user data
    # Add Gender column if it doesn't exist
    if 'Gender' not in df_users.columns:
        np.random.seed(42)
        df_users['Gender'] = np.random.choice(['Laki-laki', 'Perempuan'], size=len(df_users), p=[0.5, 0.5])
    
    # Add Age_Group column
    df_users['Age_Group'] = df_users['Age'].apply(get_age_group)
    
    # Extract province from location
    df_users['Location'] = df_users['Location'].str.split(', ').str[1]
    
    # Process rating data
    # Add trip type if it doesn't exist
    if 'Tipe_Perjalanan' not in df_ratings.columns:
        np.random.seed(42)
        df_ratings['Tipe_Perjalanan'] = np.random.choice(
            ['Friends Trip', 'Family Trip', 'Couple Trip', 'Solo Trip'], 
            size=len(df_ratings), 
            p=[0.35, 0.30, 0.25, 0.10]
        )
    
    # Filter high-rated places
    # Merge datasets
    ratings_with_places = pd.merge(
        df_ratings, 
        data_tourism_processed[['Place_Id', 'Place_Name', 'Category']], 
        on='Place_Id', 
        how='left'
    )
    
    full_data = pd.merge(
        ratings_with_places, 
        df_users.rename(columns={'Location': 'User Location'}), 
        on='User_Id', 
        how='left'
    )
    
    # Filter ratings >= 4
    df_filteredrating = full_data[full_data['Place_Ratings'] >= 4]
    
    # Generate rules
    rules_data = df_filteredrating.groupby(
        ['Category', 'Gender', 'Age_Group']
    ).agg({
        'User Location': lambda x: x.mode()[0],
        'Tipe_Perjalanan': lambda x: x.mode()[0],
        'User_Id': 'count'
    }).reset_index().rename(columns={'User_Id': 'Total_Users'})
    
    # Sort by Total_Users
    rules_data = rules_data.sort_values(by=['Category', 'Total_Users'], ascending=[True, False]).reset_index(drop=True)
    
    # Train and save encoder
    encoder = OneHotEncoder()
    encoder.fit(rules_data[['Gender', 'Age_Group']])
    
    with open(f'{models_dir}/encoder.pkl', 'wb') as f:
        pickle.dump(encoder, f)
    
    # Save processed files
    data_tourism_processed.to_csv(f'{output_dir}/tourism_processed.csv', index=False)
    rules_data.to_csv(f'{output_dir}/rules_data.csv', index=False)
    
    return {
        'tourism_count': len(data_tourism_processed),
        'rules_count': len(rules_data)
    }

def get_age_group(age):
    """Convert numerical age to age group."""
    if 18 <= age <= 22:
        return 'Teen/College'
    elif 23 <= age <= 27:
        return 'Young Adult'
    elif 28 <= age <= 32:
        return 'Adult'
    else:
        return 'Mature Adult'

if __name__ == "__main__":
    # Define paths
    tourism_path = 'data/raw/tourism_with_id.csv'
    user_path = 'data/raw/user.csv'
    rating_path = 'data/raw/tourism_rating.csv'
    output_dir = 'data/processed'
    models_dir = 'models'
    
    # Run preprocessing
    result = preprocess_data(tourism_path, user_path, rating_path, output_dir, models_dir)
    
    print(f"Preprocessing completed successfully!")
    print(f"Total tourism places: {result['tourism_count']}")
    print(f"Total rules generated: {result['rules_count']}")