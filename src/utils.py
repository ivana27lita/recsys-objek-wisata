import pandas as pd

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