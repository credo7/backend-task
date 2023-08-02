from typing import Optional, Any

import pymongo


class MongoService:
    def __init__(self, hostname: str, port: int, db_name: str, col_name: str):
        self._client = pymongo.MongoClient(f'mongodb://{hostname}:{port}/')
        self._urls_col = self._client[db_name][col_name]
        self._create_indexes()

    def _create_indexes(self) -> None:
        index_info = self._urls_col.index_information()
        if 'short_url_path_1' not in index_info:
            self._urls_col.create_index('short_url_path', unique=True)

        if 'long_url_1' not in index_info:
            self._urls_col.create_index('long_url', unique=True)

    def _find_one_by_key_value(self, find_key: str, value: str, selected_key: str) -> Optional[Any]:
        """
                Finds a single document in the collection based on the provided key-value pair and returns the value of the selected field.

                Args:
                    find_key (str): The key to search for in the documents.
                    value (str): The value to match with the find_key.
                    selected_key (str): The field name whose value will be returned.

                Returns:
                    Any: The value of the selected field in the found document, or None if not found.
        """
        selected_data = self._urls_col.find_one({find_key: value}, {'_id': 0, selected_key: 1})
        return selected_data.get(selected_key) if selected_data else None

    def insert_url_mapping(self, short_url_path: str, long_url: str):
        """
                Inserts a new URL mapping document into the collection with the provided short URL path, long URL, and initializes the 'visits' field to 0.

                Args:
                    short_url_path (str): The short URL path to insert.
                    long_url (str): The long URL to insert.

                Returns:
                    pymongo.results.InsertOneResult: The result of the insert operation.
        """
        return self._urls_col.insert_one({'short_url_path': short_url_path, 'long_url': long_url, 'visits': 0})

    def is_short_url_path_exist(self, path: str) -> bool:
        return bool(self._find_one_by_key_value(find_key='short_url_path', value=path, selected_key='short_url_path'))

    def find_short_url_path_by_long_url(self, long_url: str) -> Optional[str]:
        return self._find_one_by_key_value(find_key='long_url', value=long_url, selected_key='short_url_path')

    def find_long_url_by_short_url_path(self, short_url_path: str) -> Optional[str]:
        return self._find_one_by_key_value(find_key='short_url_path', value=short_url_path, selected_key='long_url')

    def increment_short_url_path_counter(self, short_url_path: str) -> None:
        """
                Increments the 'visits' counter for the given short URL path in the collection.

                Args:
                    short_url_path (str): The short URL path whose counter needs to be incremented.

                Returns:
                    None
        """
        self._urls_col.update_one({'short_url_path': short_url_path}, {'$inc': {'visits': 1}})

    def find_short_url_path_visits(self, short_url_path: str) -> int:
        """
                Retrieves the number of visits for the given short URL path.

                Args:
                    short_url_path (str): The short URL path to retrieve the number of visits for.

                Returns:
                    int: The number of visits for the given short URL path.
        """
        return self._find_one_by_key_value(find_key='short_url_path', value=short_url_path, selected_key='visits')
