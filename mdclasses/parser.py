from pathlib import Path
import re
from abc import ABC, abstractmethod
from lxml.etree import QName, ElementTree, Element, tostring, parse
from typing import Dict, List, Union

from mdclasses.conf_base import ABCConfigParser, ABCObjectParser, ConfObject
from mdclasses.configuration_enums import ObjectType, Format


class XMLParser:

    def __init__(self, file: Union[str, Path], obj_type: ObjectType):
        self.file = Path(file)
        self.obj_type = obj_type

    @abstractmethod
    def parse(self) -> (str, list, str, dict):
        pass


def get_parser(file: Union[str, Path], obj_type: ObjectType,
               export_type: Format = Format.CONFIGURATOR) -> Union['PureXMLConfigParser', 'PureXMLObjectParser']:
    if export_type == Format.CONFIGURATOR:
        if obj_type == ObjectType.CONFIGURATION:
            return PureXMLConfigParser(file, obj_type)
        else:
            return PureXMLObjectParser(file, obj_type)
    else:
        raise NotImplementedError


class PureXMLParser(XMLParser, ABC):

    def __init__(self, file: Union[str, Path], obj_type: ObjectType):
        super(PureXMLParser, self).__init__(file, obj_type)
        self._root = None
        self._encoding = 'utf-8'

    def _get_root(self) -> ElementTree():

        if self._root is not None:
            return self._root
        with self.file.open('r', encoding=self._encoding) as f:
            tree = parse(f)

        root = tree.getroot()

        obj_tag = root.xpath(f'//tns:{self.obj_type.value}', namespaces={'tns': root.nsmap[None]})

        if len(obj_tag) == 0:
            raise ValueError(f'Не найден объект по типу {self.obj_type.value} в файле {self.file}')
        self._root = obj_tag[0]

        return self._root


class PureXMLConfigParser(PureXMLParser, ABCConfigParser):

    def parse(self) -> (str, list, str, dict):
        return self._parse_configuration()

    def _parse_configuration(self) -> (str, list, str, dict):

        configuration = self._get_root()

        childes = []
        uuid = _get_uuid(configuration)
        name_obj = _get_property(configuration, 'Name')[0]
        name = name_obj.text

        properties = _read_properties(configuration)

        child_objs = _get_childes(configuration)

        for child_obj in child_objs:
            childes.append(dict(
                obj_type=QName(child_obj).localname,
                obj_name=child_obj.text,
                line_number=child_obj.sourceline
            ))

        return uuid, childes, name, properties

    def object_list(self) -> List[str]:
        configuration = self._get_root()
        child_objs = _get_childes(configuration)
        return [f'{QName(child_obj).localname}.{child_obj.text}' for child_obj in child_objs]

    def add_objects_to_configuration(self, objects: List[ConfObject]):
        if not objects:
            return
        conf = self._get_root()
        child_objects = conf.find('.//ChildObjects', namespaces=conf.nsmap)

        for obj in objects:
            child = Element(str(obj.obj_type.value))
            child.text = obj.name
            child_objects.append(child)
        with open(self.file, r'wb') as f:
            f.write(
                tostring(conf.getparent(), xml_declaration=True, encoding=self._encoding, pretty_print=True)
            )


class PureXMLObjectParser(PureXMLParser, ABCObjectParser):

    def parse(self) -> (str, list, str, dict):
        return self._parse_object()

    def _parse_object(self) -> (str, list, str, dict):

        obj = self._get_root()

        childes = dict(
            attributes=list(),
            forms=list(),
            templates=list(),
            commands=list(),
            others=list()
        )
        uuid = _get_uuid(obj)
        child_objs = _get_childes(obj)
        name_obj = _get_property(obj, 'Name')[0]

        properties = _read_properties(obj)

        if self.obj_type in [
            ObjectType.SUBSYSTEM,
        ]:
            return uuid, childes, name_obj.sourceline, properties

        for child_obj in child_objs:
            set_child_by_tag(childes, child_obj)

        return uuid, childes, name_obj.sourceline, properties


class SupportConfigurationParser:
    REG_EXP = r'(?:,|\\n|^)(\"(?:(?:\"\")*[^\"]*)*\"|[^\",\\n]*|(?:\\n|$))'

    FILE_CONF_NUMBER = 2

    CONF_VERSION_SHIFT = 3
    CONF_PROVIDER_SHIFT = 4
    CONF_NAME_SHIFT = 5
    CONF_OBJECTS_SHIFT = 6

    OBJECT_TUPLE_LEN = 4
    OBJECT_SUPPORT_TYPE_SHIFT = 0
    OBJECT_UUID_SHIFT = 2

    '''
    Описание формата по позиции в картеже описании элемента:
        0 - support_type;
        2 - UUID элмента 
    '''

    def __init__(self, file_path: Union[str, Path]):
        self.file_path = Path(file_path)

    def parse(self) -> dict:
        conf_data = {}
        if not self.file_path.exists():
            return dict()

        data = self.file_path.read_text(encoding='utf-8-sig')

        file_reg_exp = re.compile(self.REG_EXP)
        file_data = file_reg_exp.findall(data)

        cur_element = 3
        cur_configuration = int(file_data[self.FILE_CONF_NUMBER])

        for conf_number in range(cur_configuration):

            conf_version = file_data[cur_element+self.CONF_VERSION_SHIFT]
            conf_provider = file_data[cur_element+self.CONF_PROVIDER_SHIFT]
            conf_name = file_data[cur_element+self.CONF_NAME_SHIFT].replace('"', '')
            cur_conf_objects = int(file_data[cur_element+self.CONF_OBJECTS_SHIFT])
            conf_objects = {}

            for object_num in range(
                    cur_element + 1 + self.CONF_OBJECTS_SHIFT,
                    cur_element + self.CONF_OBJECTS_SHIFT + cur_conf_objects * self.OBJECT_TUPLE_LEN,
                    self.OBJECT_TUPLE_LEN):
                object_support_type = int(file_data[object_num + self.OBJECT_SUPPORT_TYPE_SHIFT])
                object_uuid = file_data[object_num + self.OBJECT_UUID_SHIFT]
                conf_objects[object_uuid] = object_support_type

            cur_element = object_num + 2 + self.OBJECT_TUPLE_LEN

            conf_data[conf_name] = dict(
                conf_version=conf_version,
                conf_provider=conf_provider,
                conf_objects=conf_objects,
            )

        return conf_data


def _get_childes(obj: ElementTree):
    return obj.xpath('./tns:ChildObjects/*', namespaces={'tns': obj.nsmap[None]})


def _get_uuid(obj: ElementTree):
    return obj.attrib['uuid']


def _parse_attr_child(obj: ElementTree):
    name_obj = _get_property(obj, 'Name')[0]
    return dict(
        uuid=_get_uuid(obj),
        name=name_obj.text,
        line_number=name_obj.sourceline
    )


def set_child_by_tag(childes: Dict[str, list], obj: ElementTree):
    tag = QName(obj).localname
    if tag == 'Form':
        pass
    elif tag == 'Template':
        pass
    elif tag == 'Command':
        pass
    elif tag in ['Recalculation', 'Table', 'Cube', 'Function']:
        pass

    elif tag in ['Attribute', 'Operation', 'Column',
                 'EnumValue', 'Resource', 'Dimension',
                 'AccountingFlag', 'ExtDimensionAccountingFlag',
                 'AddressingAttribute']:
        childes['attributes'].append(_parse_attr_child(obj))
    elif tag in ['TabularSection', 'URLTemplate']:
        tabular_data = _parse_attr_child(obj)
        tabular_data['attributes'] = [_parse_attr_child(tab_attr) for tab_attr in _get_childes(obj)]
        childes['attributes'].append(tabular_data)
    else:
        raise ValueError(f'Не описан tag {tag}')


def _get_property(obj: ElementTree, tag_name: str):
    return obj.xpath(f'./tns:Properties/tns:{tag_name}', namespaces={'tns': obj.nsmap[None]})


def _read_properties(obj: ElementTree):
    props = {}
    for el in obj.xpath(f'./tns:Properties/*', namespaces={'tns': obj.nsmap[None]}):
        tag = QName(el).localname
        if len(el) == 0:
            val = el.text
        else:
            val = _read_properties(el)
        props[tag] = val
    return props
