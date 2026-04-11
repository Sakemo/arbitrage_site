import toml
from .util import get_current_dollar_value

class Config:
    def __init__(self, config_file):
        self.config_data = toml.load(config_file)

    @property
    def bot_token(self):
        return self.config_data["token"]["bot"]

    @property
    def group_id(self):
        return self.config_data["group"]["id"]

    @property
    def email(self):
        return self.config_data["credentials"]["email"]

    @property
    def buy_exchanges(self):
        return self.config_data["exchange"]["buy_exchanges"]

    @property
    def sell_exchanges(self):
        return self.config_data["exchange"]["sell_exchanges"]

    @property
    def dollar_value(self):
        if self.config_data["finance"].get("automatic_dollar_value"):
            dollar = get_current_dollar_value()
            if dollar != 0:
                return float(dollar)
            else:
                return float(self.config_data["finance"]["dollar_value"])
        return float(self.config_data["finance"]["dollar_value"])

    @property
    def secret_key(self):
        return self.config_data["flask"]["secret_key"]

    @property
    def database_uri(self):
        return self.config_data["flask"]["database_uri"]

    @property
    def auth_database_uri(self):
        return self.config_data["flask"]["auth_database_uri"]
