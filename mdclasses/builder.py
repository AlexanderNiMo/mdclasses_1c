from os import path
from json import load, dump
from mdclasses.parser import XMLParser, SupportConfigurationParser
from mdclasses.conf_base import ObjectType, Configuration, resolve_path


def read_configuration(config_dir: str) -> Configuration:
    conf = create_configuration(config_dir)
    read_configuration_objects(conf)
    conf.set_support(get_support_data(config_dir))

    return conf


def create_configuration(config_dir: str):

    config_data = path.join(config_dir, resolve_path(ObjectType.CONFIGURATION))
    parser = XMLParser(config_data, ObjectType.CONFIGURATION)

    uuid, child_data, name, props = parser.parse_configuration()

    return Configuration(uuid=uuid, conf_objects=child_data, root_path=config_dir, name=name, props=props)


def get_support_data(config_dir: str):
    support_path = path.abspath(path.join(config_dir, 'Ext/ParentConfigurations.bin'))
    parser = SupportConfigurationParser(support_path)
    return parser.parse()


def read_configuration_objects(conf: Configuration):

    for conf_object in conf.conf_objects:

        object_config = path.join(
            conf.root_path,
            resolve_path(conf_object.obj_type, conf_object.name)
        )
        parser = XMLParser(object_config, conf_object.obj_type)
        conf_object.uuid, obj_childes, conf_object.line_number, conf_object.props = parser.parse_object()
        conf_object.set_childes(obj_childes)


def save_to_json(config_dir, json_path):
    conf = read_configuration(config_dir)
    data = conf.to_dict()
    with open(json_path, r'w') as f:
        dump(data, f)


def read_from_json(json_path: str):
    with open(json_path, 'r') as f:
        data = load(f)
        conf = Configuration.from_dict(data)
