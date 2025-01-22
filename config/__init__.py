from environ import config, to_config, var
from nomnom.convention import SystemConfiguration as NomnomSystemConfiguration


@config(prefix="NOM")
class SystemConfiguration(NomnomSystemConfiguration):
    controll_jwt_key = var()


system_configuration = to_config(SystemConfiguration)
