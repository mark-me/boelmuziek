import logging
from dateutil import parser

logging.basicConfig(
    format='%(levelname)s:\t%(asctime)s - %(module)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def rename_song_dict_keys(data):
    """
    Rename the song key within a list of dictionaries or a single dictionary.

    Parameters:
    - data: List of dictionaries or a single dictionary

    Returns:
    - A new list of dictionaries or a new dictionary with the key renamed from 'title' to 'song'
    """
    old_key_name = 'title'
    new_key_name = 'song'

    if isinstance(data, list):
        # If data is a list of dictionaries
        return [{new_key_name if key == old_key_name else key: value for key, value in item.items()} for item in data]
    elif isinstance(data, dict):
        # If data is a single dictionary
        if old_key_name in data:
            data[new_key_name] = data.pop(old_key_name)
        return data
    else:
        # Handle other types or raise an exception if needed
        raise ValueError("Input data must be a list of dictionaries or a single dictionary.")

def type_library(data):
    """Converts datatypes to their actual datatypes instead of the strings MPD returns

    Args:
        data (dict or list): A dictionary containing MPD library query results

    Returns:
        dict or list: A (list of) dictionary with converted data types
    """
    if isinstance(data, list):
        # If data is a list of dictionaries
        i = 0
        while i < len(data):
            data[i] = type_library_dict(data[i])
            i += 1
        return data
    elif isinstance(data, dict):
        # If data is a single dictionary
        return type_library_dict(data)
    else:
        # Handle other types or raise an exception if needed
        raise ValueError("Input data must be a list of dictionaries or a single dictionary.")

def type_library_dict(data) -> dict:
    """Converts datatypes to their actual datatypes instead of the strings MPD returns

    Args:
        data (dict): A dictionary containing MPD library query results

    Returns:
        dict: A dictionary with converted data types
    """
    lst_key_int = ['track', 'disc', 'time']
    lst_key_datetime = ['last-modified']
    lst_float = ['duration']

    for key in lst_key_int:
        if key in data.keys():
            logger.debug(f"Converting {key} of {data['file']} to int.")
            try:
                data[key] = int(data[key])
            except TypeError:
                logger.error(f"Could not convert {key} of {data['file']} to int.")

    for key in lst_key_datetime:
        if key in data.keys():
            logger.debug(f"Converting {key} of {data['file']} to datetime.")
            try:
                data[key] =  parser.parse(data[key])
            except TypeError:
                logger.error(f"Could not convert {key} of {data['file']} to datetime.")
    for key in lst_float:
        if key in data.keys():
            logger.debug(f"Converting {key} of {data['file']} to float.")
            try:
                data[key] = float(data[key])
            except TypeError:
                logger.error(f"Could not convert {key} of {data['file']} to float.")
    return data

def nest_artist_album(list_dict_files):
    """
    Nesting of files within a hierarchy of artists and their albums

    Parameters:
    - list_dict_files: List of dictionaries that represent music files

    Returns:
    - list of dictionaries that are grouped in a hierarchy by artist and album
    """
    # Initialize a dictionary to store the result
    result_dict = {}

    # Iterate over each dictionary in the list
    for file_data in list_dict_files:
        artist = file_data['artist']
        album = file_data.get('album', '')  # Get 'album' with a default value of an empty string
        file_dict = {key: value for key, value in file_data.items() if key not in ['artist', 'album']}

        # Check if the artist is already in the result_dict
        if artist in result_dict:
            # Check if the album is already in the artist's dictionary
            if album in result_dict[artist]:
                result_dict[artist][album]['files'].append(file_dict)
            else:
                result_dict[artist][album] = {'album': album, 'files': [file_dict]}
        else:
            result_dict[artist] = {album: {'album': album, 'files': [file_dict]}}

    # Convert the result_dict to a list of dictionaries
    result_list = [{'artist': artist, 'albums': list(albums.values())} for artist, albums in result_dict.items()]

    return result_list

def nest_album(list_dict_files):
    """
    Nesting of files within a hierarchy of albums

    Parameters:
    - list_dict_files: List of dictionaries that represent music files

    Returns:
    - list of dictionaries that are grouped in a hierarchy by album
    """
    # Initialize a dictionary to store the result
    result_dict = {}

    # Iterate over each dictionary in the list
    for file_data in list_dict_files:
        album = file_data.get('album', '')  # Get 'album' with a default value of an empty string
        file_dict = {key: value for key, value in file_data.items() }#if key not in ['file']}

        # Check if the album is already in the result_dict
        if album in result_dict:
            result_dict[album]['files'].append(file_dict)
        else:
            result_dict[album] = {'album': album, 'files': [file_dict]}

    # Convert the result_dict to a list of dictionaries
    result_list = list(result_dict.values())

    return result_list

def determine_image_format(image_data: bytes) -> str:
    """Function to determine image format (PNG or JPG) based on magic bytes

    Args:
        image_data (bytes): A byte stream that represents an image

    Raises:
        ValueError: When encountering a different format than either PNG or JPG

    Returns:
        str: A MIME type string
    """
    if image_data.startswith(b'\x89PNG\r\n\x1a\n'):
        return "image/png"
    elif image_data.startswith(b'\xff\xd8'):
        return "image/jpeg"
    else:
        raise ValueError("Unsupported image format")