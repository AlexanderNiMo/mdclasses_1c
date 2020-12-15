from typing import Union
from pathlib import Path
from json import load, dump


from mdclasses.parser import get_parser, SupportConfigurationParser
from mdclasses.conf_base import Configuration, SubSystem
from mdclasses.utils.path_resolver import get_path_resolver
from mdclasses.configuration_enums import ObjectType, Format


def read_configuration(config_dir: str) -> Configuration:
    conf = create_configuration(config_dir)
    read_configuration_objects(conf)
    conf.set_support(get_support_data(config_dir))

    return conf


def create_configuration(config_dir: Union[str, Path], file_format: Format = Format.CONFIGURATOR):

    path_resolver = get_path_resolver(file_format)

    config_data = Path(config_dir).joinpath(path_resolver.conf_file_path(ObjectType.CONFIGURATION))
    parser = get_parser(config_data, ObjectType.CONFIGURATION)

    uuid, child_data, name, props = parser.parse()

    return Configuration(uuid=uuid, conf_objects=child_data, root_path=config_dir,
                         name=name, props=props, parser=parser, file_format=file_format)


def get_support_data(config_dir: Union[str, Path]):
    config_dir = Path(config_dir)
    support_path = config_dir.joinpath('Ext/ParentConfigurations.bin').absolute()
    parser = SupportConfigurationParser(support_path)
    return parser.parse()


def read_configuration_objects(conf: Configuration):

    for conf_object in conf.conf_objects:

        conf_object.uuid, obj_childes, conf_object.line_number, conf_object.props = read_configuration_object(conf_object)
        conf_object.set_childes(obj_childes)

        if conf_object.obj_type != ObjectType.SUBSYSTEM:
            continue

        handle_child_subsystems(conf, conf_object, obj_childes)


def read_configuration_object(conf_object):
        object_config = conf_object.file_name
        parser = get_parser(object_config, conf_object.obj_type)
        return parser.parse()


def handle_child_subsystems(conf: Configuration, obj: SubSystem, obj_childes: dict):

    for subsystem in filter(lambda ch: ch[0] == 'Subsystem', obj_childes['others']):
        conf_obj = SubSystem(
            name=subsystem[1],
            parent=obj
        )
        conf_obj.uuid, obj_childes, conf_obj.line_number, conf_obj.props = read_configuration_object(conf_obj)
        conf_obj.set_childes(obj_childes)
        conf.conf_objects.append(conf_obj)
        handle_child_subsystems(conf, conf_obj, obj_childes)


def save_to_json(conf: Configuration, json_path: [str, Path]):
    json_path = Path(json_path)
    data = conf.to_dict()
    with json_path.open('w', encoding='utf-8') as f:
        dump(data, f, ensure_ascii=False)


def read_from_json(json_path: Union[str, Path]):
    json_path = Path(json_path)
    with json_path.open(r'r', encoding='utf-8') as f:
        data = load(f)
    return Configuration.from_dict(data)
