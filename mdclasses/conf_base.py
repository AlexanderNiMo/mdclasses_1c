from _ast import For
from typing import List, Dict, Union, Optional
from pathlib import Path
from abc import ABC, abstractmethod
import shutil

from mdclasses.configuration_enums import ObjectType, SupportType, Format
from mdclasses.Module import Module, create_module, ModuleParser
from mdclasses.Form import Form
from mdclasses.utils.path_resolver import get_path_resolver, ABCPathResolver


class Serializable(ABC):

    @abstractmethod
    def to_dict(self):
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, args, kwargs):
        pass
    

class Supportable(Serializable):

    def __init__(self, uuid: str = ''):
        self.uuid = uuid
        self.support_type = SupportType.NONE_SUPPORT

    def set_support(self, support: dict):
        try:
            self.support_type = SupportType(support[self.uuid])
        except KeyError:
            self.support_type = SupportType.NONE_SUPPORT

    @property
    def on_support(self) -> bool:
        return self.support_type in [
            SupportType.NOT_EDITABLE,
            SupportType.EDITABLE_SUPPORT_ENABLED,
            SupportType.NOT_SUPPORTED
        ]
    
    def to_dict(self):
        return dict(
            uuid=self.uuid,
            support_type=self.support_type.value
        )

    @classmethod
    def from_dict(cls, *args, **kwargs):
        data = args[0] if 'data' not in kwargs else kwargs['data']

        obj = cls(data['uuid']) if 'obj' not in kwargs else kwargs['obj']

        obj.uuid = data['uuid']
        obj.set_support(data['support_type'])


class ConfObject(Supportable):

    def __init__(self, name: str, obj_type: Union[ObjectType, str], parent: 'Configuration',
                 line_number: int = 0, props: dict = None, file_format: Format = Format.CONFIGURATOR):
        super(ConfObject, self).__init__()

        self.file_format = file_format
        self.__path_resolver: Optional[ABCPathResolver] = None

        if props is None:
            props = {}

        self.line_number = line_number

        self.parent = parent
        self.name = name

        self.props = props

        self.modules: List[Module] = list()

        if isinstance(obj_type, str):
            self.obj_type = ObjectType(obj_type)
        else:
            self.obj_type = obj_type

        self.forms: List[Form] = list()
        self.templates = list()
        self.commands = list()
        self.attributes: List[ObjectAttribute] = list()

    @property
    def path_resolver(self) -> ABCPathResolver:
        if self.__path_resolver is None:
            self.__path_resolver = get_path_resolver(self.file_format)
        return self.__path_resolver

    @property
    def full_name(self):
        return f'{self.obj_type.value}.{self.name}'

    @property
    def file_name(self) -> Path:
        return self.root_path.joinpath(self.path_resolver.conf_file_path(self.obj_type, self.name))

    @property
    def root_path(self) -> Path:
        return self.parent.root_path

    @property
    def obj_type_dir(self) -> Path:
        return self.file_name.parent

    @property
    def obj_dir(self) -> Path:
        return self.ext_path.parent

    @property
    def form_path(self):
        return self.root_path.joinpath(self.path_resolver.form_path(self.obj_type, self.name))

    @property
    def ext_path(self) -> Path:
        return self.root_path.joinpath(self.path_resolver.ext_path(self.obj_type, self.name)).absolute()

    def read_modules(self):
        ext_path = self.ext_path

        if not ext_path.exists():
            return

        parser = ModuleParser()

        for element in ext_path.iterdir():
            if element.is_file() and element.suffix == '.bsl':
                self.modules.append(create_module(parser, element, self))

    def read_forms(self):
        self.forms = []

        forms_path = self.form_path

        if not forms_path.exists():
            return

        forms = {}

        for element in forms_path.iterdir():
            if element.is_file() and element.suffix == '.xml':
                name = element.stem
                if name in forms:
                    forms[name]['description_path'] = element
                else:
                    forms[name] = dict(description_path=element, structure_path='')
            elif element.is_dir():
                struct_path = element.joinpath('Ext', 'Form', 'Form.xml')
                name = element.stem
                if name in forms:
                    forms[name]['structure_path'] = struct_path
                else:
                    forms[name] = dict(description_path='', structure_path=struct_path)

        self.forms.extend(
            [Form(**v) for v in forms.values()]
        )

    def set_support(self, support: dict):

        super(ConfObject, self).set_support(support)

        for form in self.forms:
            form.set_support(support)

        for template in self.templates:
            template.set_support(support)

        for command in self.commands:
            command.set_support(support)

        for attribute in self.attributes:
            attribute.set_support(support)

    def set_childes(self, childes: Dict[str, list]):
        self.set_attributes(childes['attributes'])
        self.set_forms(childes['forms'])
        self.set_templates(childes['templates'])
        self.set_commands(childes['commands'])

    def set_forms(self, forms):
        pass

    def set_templates(self, templates):
        pass

    def set_commands(self, commands):
        pass

    def set_attributes(self, attributes: List[dict]):
        for attr_data in attributes:
            self.attributes.append(ObjectAttribute.from_dict(attr_data, self))

    def to_dict(self):
        data = super(ConfObject, self).to_dict()
        data.update(
            dict(
                name=self.name,
                obj_type=self.obj_type.value,
                attributes=[attr.to_dict() for attr in self.attributes],
                forms=[form.to_dict() for form in self.forms],
                templates=[template.to_dict() for template in self.templates],
                commands=[command.to_dict() for command in self.commands],
                line_number=self.line_number,
                file_format=self.file_format.value
            )
        )
        return data

    @classmethod
    def from_dict(cls, data: dict, parent: 'Configuration'):
        obj = cls(
            name=data['name'],
            parent=parent,
            line_number=data['line_number'],
            obj_type=data['obj_type'],
            file_format=Format(data['file_format'])
        )

        obj.uuid = data['uuid'],
        obj.set_childes(data)
        return obj

    def __repr__(self):
        return f'<ConfObject: {self.full_name}>'


class ObjectAttribute(Supportable):

    def __init__(self, name: str, uuid: str, parent: Union[ConfObject, 'ObjectAttribute'], line_number: int):
        super(ObjectAttribute, self).__init__(uuid)
        self.parent: Union[ConfObject, 'ObjectAttribute'] = parent
        self.name: str = name
        self.attributes: List[ObjectAttribute] = list()
        self.line_number: int = line_number

    def set_attributes(self, attributes: List[dict]):
        for attr_data in attributes:
            self.attributes.append(self.from_dict(attr_data, self))

    @property
    def file_name(self):
        return self.parent.file_name

    @property
    def full_name(self):
        return f'{self.parent.full_name}.{self.name}'

    def set_support(self, support: dict):
        super(ObjectAttribute, self).set_support(support)

        for attr in self.attributes:
            attr.set_support(support)

    @classmethod
    def from_dict(cls, attr_data: dict, parent: Union[ConfObject, 'ObjectAttribute']) -> 'ObjectAttribute':
        attr = cls(
            name=attr_data['name'],
            uuid=attr_data['uuid'],
            parent=parent,
            line_number=attr_data['line_number']
        )
        if 'attributes' in attr_data:
            attr.set_attributes(attr_data['attributes'])
        return attr

    def to_dict(self):
        data = super(ObjectAttribute, self).to_dict()
        data.update(
            dict(
                name=self.name,
                attributes=[attr.to_dict() for attr in self.attributes],
                line_number=self.line_number
            )
        )
        return data

    @property
    def root_path(self):
        return self.parent.root_path

    def __repr__(self):
        return f'<ObjectAttribute: {self.parent}.{self.name}>'


class Configuration(Supportable):

    def __init__(self, uuid: str, props: dict, conf_objects: List[dict], root_path: Path, name: str,
                 parser: 'ABCConfigParser', file_format: Format = Format.CONFIGURATOR):
        super(Configuration, self).__init__(uuid)

        self._parser: 'ABCConfigParser' = parser
        self.name = name
        self.root_path = Path(root_path)
        self.file_format = file_format

        self.conf_objects = [
            ConfObject(
                name=conf_obj['obj_name'],
                obj_type=conf_obj['obj_type'],
                parent=self
            ) for conf_obj in conf_objects
        ]
        self.support_type = SupportType.NONE_SUPPORT
        self.props = props
        self.__path_resolver: Optional[ABCPathResolver] = None

    @property
    def path_resolver(self):
        if self.__path_resolver is None:
            self.__path_resolver = get_path_resolver(self.file_format)
        return self.__path_resolver

    def set_support(self, support_data: dict):
        conf_support = {}

        for key in support_data:
            if key == self.name:
                continue
            conf_support.update(support_data[key]['conf_objects'])

        super(Configuration, self).set_support(conf_support)

        for obj in self.conf_objects:
            obj.set_support(conf_support)

    def get_object(self, name: str, obj_type: Union[ObjectType, str]) -> ConfObject:
        cur_obj_type = obj_type
        if isinstance(obj_type, str):
            cur_obj_type = ObjectType(obj_type)

        data = list(filter(lambda obj: obj.obj_type == cur_obj_type and obj.name == name, self.conf_objects))
        try:
            return data[0]
        except IndexError:
            raise IndexError(f'Объект не найден! Имя:{name} Тип:{obj_type}')

    def add_object(self, obj: ConfObject):
        try:
            self.get_object(obj.name, obj.obj_type)
        except IndexError:
            new_object = obj
        else:
            raise ValueError(f'Объект {obj} уже есть в конфигурации')
        if obj.parent.root_path != self.root_path:
            new_object = self.clone_object(obj)

        self.conf_objects.append(new_object)

        return new_object

    def clone_object(self, obj: ConfObject) -> ConfObject:
        data_dict = obj.to_dict()
        new_object = ConfObject.from_dict(data_dict, self)

        type_path = new_object.obj_type_dir

        if not type_path.exists():
            type_path.mkdir()

        shutil.copytree(obj.obj_dir, new_object.obj_dir)
        shutil.copy(obj.file_name, new_object.file_name)

        return new_object

    @property
    def file_name(self) -> Path:
        return self.root_path.joinpath(self.path_resolver.conf_file_path(ObjectType.CONFIGURATION, self.name))

    @classmethod
    def from_dict(cls, data):
        conf = cls(
            uuid=data['uuid'],
            name=data['name'],
            root_path=Path(''),
            conf_objects=list(),
            props=data['props'],
            parser=data.get('parser'),
            file_format=Format(data.get('file_format'))
        )
        conf.conf_objects = [ConfObject.from_dict(obj_data, conf) for obj_data in data['conf_objects']]
        return conf

    def to_dict(self):
        data = super(Configuration, self).to_dict()
        data.update(
             dict(
                name=self.name,
                uuid=self.uuid,
                conf_objects=[obj.to_dict() for obj in self.conf_objects],
                props=self.props,
                file_format=self.file_format.value,
            )
        )
        return data

    def save_to_file(self):

        cur_objects = set([obj.full_name for obj in self.conf_objects])
        file_obj = set(self._parser.object_list())
        new_objects_str = [el.split('.') for el in cur_objects - file_obj]

        self._parser.add_objects_to_configuration([self.get_object(el[1], el[0]) for el in new_objects_str])

    def __repr__(self):
        return f'<Configuration: {self.name} {self.root_path}>'


class ABCConfigParser(ABC):

    @abstractmethod
    def object_list(self) -> List[str]:
        pass

    @abstractmethod
    def add_objects_to_configuration(self, objects: List[ConfObject]):
        pass


class ABCObjectParser(ABC):
    pass
