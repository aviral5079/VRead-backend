import os


class Utils:
    db_path = ""

    @classmethod
    def set_db_path(self, path):
        Utils.db_path = path

    @classmethod
    def get_db_path(self):
        return Utils.db_path
