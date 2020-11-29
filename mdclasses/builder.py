from typing import Union
from pathlib import Path
from json import load, dump
from mdclasses.parser import get_parser, SupportConfigurationParser
from mdclasses.conf_base import ObjectType, Configuration, resolve_path


def read_configuration(config_dir: str) -> Configuration:
    conf = create_configuration(config_dir)
    read_configuration_objects(conf)
    conf.set_support(get_support_data(config_dir))

    return conf


def create_configuration(config_dir: Union[str, Path]):

    config_data = Path(config_dir).joinpath(resolve_path(ObjectType.CONFIGURATION))
    parser = get_parser(config_data, ObjectType.CONFIGURATION)

    uuid, child_data, name, props = parser.parse()

    return Configuration(uuid=uuid, conf_objects=child_data, root_path=config_dir,
                         name=name, props=props, parser=parser)


def get_support_data(config_dir: Union[str, Path]):
    config_dir = Path(config_dir)
    support_path = config_dir.joinpath('Ext/ParentConfigurations.bin').absolute()
    parser = SupportConfigurationParser(support_path)
    return parser.parse()


def read_configuration_objects(conf: Configuration):

    for conf_object in conf.conf_objects:

        object_config = conf.root_path.joinpath(resolve_path(conf_object.obj_type, conf_object.name))
        parser = get_parser(object_config, conf_object.obj_type)
        conf_object.uuid, obj_childes, conf_object.line_number, conf_object.props = parser.parse()
        conf_object.set_childes(obj_childes)


def save_to_json(conf: Configuration, json_path: [str, Path]):
    json_path = Path(json_path)
    data = conf.to_dict()
    with json_path.open('w', encoding='utf-8') as f:
        dump(data, f)


def read_from_json(json_path: Union[str, Path]):
    json_path = Path(json_path)
    with json_path.open(r'r', encoding='utf-8') as f:
        data = load(f)
    return Configuration.from_dict(data)
